import logging
import secrets
from datetime import timedelta

from django.contrib.auth.hashers import check_password, make_password
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.files.models import File, FileShare, SharedLink
from apps.files.serializers import FileSerializer, FileShareSerializer, SharedLinkSerializer
from apps.folders.models import Folder, FolderPermission
from .models import ShareInvitation, ShareActivity
from .serializers import (
    ShareInvitationSerializer,
    CreateShareInvitationSerializer,
    CreateSharedLinkSerializer,
    SharedLinkAccessSerializer,
    BulkShareSerializer,
    ShareActivitySerializer,
)

logger = logging.getLogger(__name__)


class ShareFileView(APIView):
    """Share a file directly with another user."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, file_id):
        file_record = get_object_or_404(
            File, pk=file_id, owner=request.user, is_trashed=False
        )

        email = request.data.get('email', '').lower().strip()
        permission = request.data.get('permission', 'view')

        if not email:
            return Response(
                {'error': 'Email is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            target_user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if target_user == request.user:
            return Response(
                {'error': 'You cannot share a file with yourself.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        share, created = FileShare.objects.update_or_create(
            file=file_record,
            shared_with=target_user,
            defaults={
                'shared_by': request.user,
                'permission': permission,
            },
        )

        ShareActivity.log(
            user=request.user,
            action='share_created' if created else 'share_updated',
            target_type='file',
            target_id=file_record.id,
            target_name=file_record.name,
            details={'shared_with': email, 'permission': permission},
            request=request,
        )

        return Response(
            FileShareSerializer(share).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class RevokeFileShareView(APIView):
    """Revoke a file share."""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, share_id):
        share = get_object_or_404(
            FileShare, pk=share_id, shared_by=request.user
        )

        ShareActivity.log(
            user=request.user,
            action='share_revoked',
            target_type='file',
            target_id=share.file.id,
            target_name=share.file.name,
            details={'revoked_from': share.shared_with.email},
            request=request,
        )

        share.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FileSharesListView(generics.ListAPIView):
    """List all shares for a specific file."""
    serializer_class = FileShareSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        file_id = self.kwargs['file_id']
        return FileShare.objects.filter(
            file_id=file_id, shared_by=self.request.user
        ).select_related('shared_by', 'shared_with')


class SharedWithMeView(generics.ListAPIView):
    """List files shared with the current user."""
    serializer_class = FileShareSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FileShare.objects.filter(
            shared_with=self.request.user
        ).select_related('file', 'shared_by', 'shared_with')


class SharedByMeView(generics.ListAPIView):
    """List files shared by the current user."""
    serializer_class = FileShareSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FileShare.objects.filter(
            shared_by=self.request.user
        ).select_related('file', 'shared_by', 'shared_with')


class CreateSharedLinkView(APIView):
    """Create a shared link for a file."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CreateSharedLinkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file_id = serializer.validated_data['file_id']
        file_record = get_object_or_404(
            File, pk=file_id, owner=request.user, is_trashed=False
        )

        password_raw = serializer.validated_data.get('password', '')
        expires_in_hours = serializer.validated_data.get('expires_in_hours')

        link = SharedLink.objects.create(
            file=file_record,
            created_by=request.user,
            token=secrets.token_urlsafe(32),
            permission=serializer.validated_data['permission'],
            password=make_password(password_raw) if password_raw else '',
            expires_at=(
                timezone.now() + timedelta(hours=expires_in_hours)
                if expires_in_hours else None
            ),
            max_downloads=serializer.validated_data.get('max_downloads'),
        )

        ShareActivity.log(
            user=request.user,
            action='link_created',
            target_type='file',
            target_id=file_record.id,
            target_name=file_record.name,
            details={'token': link.token[:8]},
            request=request,
        )

        return Response(
            SharedLinkSerializer(link, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class SharedLinkDetailView(generics.RetrieveDestroyAPIView):
    """Retrieve or deactivate a shared link."""
    serializer_class = SharedLinkSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SharedLink.objects.filter(created_by=self.request.user)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=['is_active', 'updated_at'])

        ShareActivity.log(
            user=self.request.user,
            action='link_deactivated',
            target_type='file',
            target_id=instance.file.id,
            target_name=instance.file.name,
            details={'token': instance.token[:8]},
        )


class SharedLinkAccessView(APIView):
    """Access a file via shared link (public endpoint)."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, token):
        link = get_object_or_404(SharedLink, token=token)

        if not link.is_accessible:
            reason = 'expired' if link.is_expired else 'limit_reached' if link.download_limit_reached else 'inactive'
            return Response(
                {'error': f'This link is no longer accessible ({reason}).'},
                status=status.HTTP_410_GONE,
            )

        if link.password:
            return Response({
                'requires_password': True,
                'file_name': link.file.name,
                'permission': link.permission,
            })

        from apps.files.services import FileDownloadService
        download_url = FileDownloadService.get_download_url(link.file)

        return Response({
            'file_name': link.file.name,
            'file_size': link.file.size,
            'mime_type': link.file.mime_type,
            'permission': link.permission,
            'download_url': download_url if link.permission == 'download' else None,
            'preview_url': download_url,
        })

    def post(self, request, token):
        """Submit password for password-protected links."""
        link = get_object_or_404(SharedLink, token=token)

        if not link.is_accessible:
            return Response(
                {'error': 'This link is no longer accessible.'},
                status=status.HTTP_410_GONE,
            )

        serializer = SharedLinkAccessSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        password = serializer.validated_data.get('password', '')
        if link.password and not check_password(password, link.password):
            return Response(
                {'error': 'Incorrect password.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        link.download_count += 1
        link.save(update_fields=['download_count', 'updated_at'])

        from apps.files.services import FileDownloadService
        download_url = FileDownloadService.get_download_url(link.file)

        return Response({
            'file_name': link.file.name,
            'file_size': link.file.size,
            'mime_type': link.file.mime_type,
            'permission': link.permission,
            'download_url': download_url,
        })


class SendInvitationView(APIView):
    """Send a share invitation."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CreateShareInvitationSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        file = folder = None

        if data.get('file_id'):
            file = get_object_or_404(
                File, pk=data['file_id'], owner=request.user, is_trashed=False
            )
        if data.get('folder_id'):
            folder = get_object_or_404(
                Folder, pk=data['folder_id'], owner=request.user, is_trashed=False
            )

        invitation = ShareInvitation.objects.create(
            invited_by=request.user,
            invited_email=data['invited_email'].lower(),
            file=file,
            folder=folder,
            permission=data['permission'],
            message=data.get('message', ''),
            expires_at=timezone.now() + timedelta(days=data.get('expires_in_days', 7)),
        )

        try:
            invited_user = User.objects.get(email=data['invited_email'].lower())
            invitation.invited_user = invited_user
            invitation.save(update_fields=['invited_user'])
        except User.DoesNotExist:
            pass

        ShareActivity.log(
            user=request.user,
            action='invitation_sent',
            target_type='file' if file else 'folder',
            target_id=file.id if file else folder.id,
            target_name=file.name if file else folder.name,
            details={'invited_email': data['invited_email']},
            request=request,
        )

        return Response(
            ShareInvitationSerializer(invitation).data,
            status=status.HTTP_201_CREATED,
        )


class InvitationListView(generics.ListAPIView):
    """List pending invitations for the current user."""
    serializer_class = ShareInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ShareInvitation.objects.filter(
            invited_email=self.request.user.email,
            status='pending',
            expires_at__gt=timezone.now(),
        )


class InvitationResponseView(APIView):
    """Accept or decline a share invitation."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        invitation = get_object_or_404(
            ShareInvitation,
            pk=pk,
            invited_email=request.user.email,
            status='pending',
        )

        if invitation.is_expired:
            invitation.status = 'expired'
            invitation.save(update_fields=['status', 'updated_at'])
            return Response(
                {'error': 'This invitation has expired.'},
                status=status.HTTP_410_GONE,
            )

        action = request.data.get('action', 'accept').lower()
        if action == 'accept':
            invitation.accept(request.user)
            ShareActivity.log(
                user=request.user,
                action='invitation_accepted',
                target_type='file' if invitation.file else 'folder',
                target_id=invitation.file.id if invitation.file else invitation.folder.id,
                target_name=invitation.file.name if invitation.file else invitation.folder.name,
                request=request,
            )
        elif action == 'decline':
            invitation.decline()
            ShareActivity.log(
                user=request.user,
                action='invitation_declined',
                target_type='file' if invitation.file else 'folder',
                target_id=invitation.file.id if invitation.file else invitation.folder.id,
                target_name=invitation.file.name if invitation.file else invitation.folder.name,
                request=request,
            )
        else:
            return Response(
                {'error': 'Action must be "accept" or "decline".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(ShareInvitationSerializer(invitation).data)


class ShareActivityListView(generics.ListAPIView):
    """List sharing activity for the current user."""
    serializer_class = ShareActivitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ShareActivity.objects.filter(
            user=self.request.user
        ).order_by('-created_at')[:100]
