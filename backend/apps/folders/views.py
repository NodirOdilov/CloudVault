import logging

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.activity.models import ActivityLog
from .models import Folder, FolderPermission
from .serializers import (
    FolderSerializer,
    FolderListSerializer,
    FolderCreateSerializer,
    FolderUpdateSerializer,
    FolderMoveSerializer,
    FolderTreeSerializer,
    FolderPermissionSerializer,
)

logger = logging.getLogger(__name__)


class FolderListView(generics.ListCreateAPIView):
    """List folders or create a new folder."""
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return FolderCreateSerializer
        return FolderListSerializer

    def get_queryset(self):
        queryset = Folder.objects.filter(
            owner=self.request.user,
            is_trashed=False,
        )

        parent_id = self.request.query_params.get('parent')
        if parent_id:
            queryset = queryset.filter(parent_id=parent_id)
        elif self.request.query_params.get('root') == 'true':
            queryset = queryset.filter(parent__isnull=True)

        starred = self.request.query_params.get('starred')
        if starred == 'true':
            queryset = queryset.filter(is_starred=True)

        return queryset.order_by('name')

    def perform_create(self, serializer):
        folder = serializer.save(owner=self.request.user)
        ActivityLog.log(
            user=self.request.user,
            action='create',
            target_type='folder',
            target_id=str(folder.id),
            target_name=folder.name,
        )


class FolderDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a specific folder."""
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return FolderUpdateSerializer
        return FolderSerializer

    def get_queryset(self):
        return Folder.objects.filter(owner=self.request.user)

    def perform_update(self, serializer):
        old_name = self.get_object().name
        instance = serializer.save()
        if instance.name != old_name:
            ActivityLog.log(
                user=self.request.user,
                action='rename',
                target_type='folder',
                target_id=str(instance.id),
                target_name=instance.name,
                details={'old_name': old_name},
            )

    def perform_destroy(self, instance):
        instance.is_trashed = True
        instance.trashed_at = timezone.now()
        instance.save(update_fields=['is_trashed', 'trashed_at', 'updated_at'])

        for descendant in instance.get_all_descendants():
            descendant.is_trashed = True
            descendant.trashed_at = timezone.now()
            descendant.save(update_fields=['is_trashed', 'trashed_at', 'updated_at'])

        from apps.files.models import File
        File.objects.filter(folder=instance, is_trashed=False).update(
            is_trashed=True,
            trashed_at=timezone.now(),
        )

        ActivityLog.log(
            user=self.request.user,
            action='trash',
            target_type='folder',
            target_id=str(instance.id),
            target_name=instance.name,
        )


class FolderMoveView(APIView):
    """Move a folder to a new parent."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        folder = get_object_or_404(Folder, pk=pk, owner=request.user, is_trashed=False)
        serializer = FolderMoveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dest_parent_id = serializer.validated_data.get('destination_parent')
        old_parent_name = folder.parent.name if folder.parent else 'Root'

        if dest_parent_id:
            dest_parent = get_object_or_404(
                Folder, id=dest_parent_id, owner=request.user, is_trashed=False
            )
            if folder.is_ancestor_of(dest_parent) or dest_parent.id == folder.id:
                return Response(
                    {'error': 'Cannot move a folder into itself or its descendants.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            folder.parent = dest_parent
        else:
            folder.parent = None

        folder.save(update_fields=['parent', 'updated_at'])
        new_parent_name = folder.parent.name if folder.parent else 'Root'

        ActivityLog.log(
            user=request.user,
            action='move',
            target_type='folder',
            target_id=str(folder.id),
            target_name=folder.name,
            details={'from': old_parent_name, 'to': new_parent_name},
        )

        return Response(FolderSerializer(folder).data)


class FolderTreeView(APIView):
    """Get the complete folder tree for the user."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        root_folders = Folder.objects.filter(
            owner=request.user,
            parent__isnull=True,
            is_trashed=False,
        ).order_by('name')
        serializer = FolderTreeSerializer(root_folders, many=True)
        return Response(serializer.data)


class FolderContentsView(APIView):
    """Get all contents (files and subfolders) of a folder."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        folder = get_object_or_404(
            Folder, pk=pk, owner=request.user, is_trashed=False
        )

        subfolders = Folder.objects.filter(
            parent=folder, owner=request.user, is_trashed=False
        ).order_by('name')

        from apps.files.models import File
        from apps.files.serializers import FileListSerializer
        files = File.objects.filter(
            folder=folder, owner=request.user, is_trashed=False
        ).order_by('-updated_at')

        return Response({
            'folder': FolderSerializer(folder).data,
            'subfolders': FolderListSerializer(subfolders, many=True).data,
            'files': FileListSerializer(files, many=True).data,
            'breadcrumb': folder.breadcrumb,
        })


class StarFolderView(APIView):
    """Toggle star status on a folder."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        folder = get_object_or_404(
            Folder, pk=pk, owner=request.user, is_trashed=False
        )
        folder.is_starred = not folder.is_starred
        folder.save(update_fields=['is_starred', 'updated_at'])
        return Response({
            'id': str(folder.id),
            'is_starred': folder.is_starred,
        })
