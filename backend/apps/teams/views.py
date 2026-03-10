import logging
from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.activity.models import ActivityLog
from apps.files.models import File
from .models import Team, TeamMembership, TeamFile, TeamInvitation
from .serializers import (
    TeamSerializer,
    TeamCreateSerializer,
    TeamUpdateSerializer,
    TeamMembershipSerializer,
    TeamMemberUpdateSerializer,
    TeamFileSerializer,
    AddTeamFileSerializer,
    TeamInvitationSerializer,
    CreateTeamInvitationSerializer,
)

logger = logging.getLogger(__name__)


class IsTeamMember(permissions.BasePermission):
    """Check if user is an active member of the team."""
    def has_permission(self, request, view):
        team_id = view.kwargs.get('team_id') or view.kwargs.get('pk')
        if not team_id:
            return False
        return TeamMembership.objects.filter(
            team_id=team_id, user=request.user, is_active=True
        ).exists()


class IsTeamAdmin(permissions.BasePermission):
    """Check if user is admin or owner of the team."""
    def has_permission(self, request, view):
        team_id = view.kwargs.get('team_id') or view.kwargs.get('pk')
        if not team_id:
            return False
        return TeamMembership.objects.filter(
            team_id=team_id, user=request.user,
            is_active=True, role__in=['owner', 'admin']
        ).exists()


class TeamListView(generics.ListCreateAPIView):
    """List user's teams or create a new team."""
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TeamCreateSerializer
        return TeamSerializer

    def get_queryset(self):
        return Team.objects.filter(
            memberships__user=self.request.user,
            memberships__is_active=True,
            is_active=True,
        ).distinct()

    def perform_create(self, serializer):
        team = serializer.save(owner=self.request.user)
        TeamMembership.objects.create(
            team=team,
            user=self.request.user,
            role='owner',
            invited_by=self.request.user,
        )
        ActivityLog.log(
            user=self.request.user,
            action='create',
            target_type='team',
            target_id=str(team.id),
            target_name=team.name,
        )


class TeamDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a team."""

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH', 'DELETE'):
            return [permissions.IsAuthenticated(), IsTeamAdmin()]
        return [permissions.IsAuthenticated(), IsTeamMember()]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return TeamUpdateSerializer
        return TeamSerializer

    def get_queryset(self):
        return Team.objects.filter(is_active=True)

    def perform_destroy(self, instance):
        if instance.owner != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only the team owner can delete the team.')
        instance.is_active = False
        instance.save(update_fields=['is_active', 'updated_at'])


class TeamMemberListView(generics.ListAPIView):
    """List team members."""
    serializer_class = TeamMembershipSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeamMember]

    def get_queryset(self):
        team_id = self.kwargs['team_id']
        return TeamMembership.objects.filter(
            team_id=team_id, is_active=True
        ).select_related('user', 'invited_by')


class TeamMemberUpdateView(APIView):
    """Update or remove a team member."""
    permission_classes = [permissions.IsAuthenticated, IsTeamAdmin]

    def patch(self, request, team_id, membership_id):
        membership = get_object_or_404(
            TeamMembership, pk=membership_id, team_id=team_id, is_active=True
        )

        if membership.role == 'owner':
            return Response(
                {'error': 'Cannot change the role of the team owner.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = TeamMemberUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        membership.role = serializer.validated_data['role']
        membership.save(update_fields=['role', 'updated_at'])

        return Response(TeamMembershipSerializer(membership).data)

    def delete(self, request, team_id, membership_id):
        membership = get_object_or_404(
            TeamMembership, pk=membership_id, team_id=team_id, is_active=True
        )

        if membership.role == 'owner':
            return Response(
                {'error': 'Cannot remove the team owner.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        membership.is_active = False
        membership.save(update_fields=['is_active', 'updated_at'])

        ActivityLog.log(
            user=request.user,
            action='team_leave',
            target_type='team',
            target_id=str(team_id),
            target_name=membership.team.name,
            details={'removed_user': membership.user.email},
        )

        return Response(status=status.HTTP_204_NO_CONTENT)


class TeamFileListView(generics.ListAPIView):
    """List files shared with a team."""
    serializer_class = TeamFileSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeamMember]

    def get_queryset(self):
        team_id = self.kwargs['team_id']
        return TeamFile.objects.filter(
            team_id=team_id
        ).select_related('file', 'added_by')


class AddTeamFileView(APIView):
    """Add a file to a team."""
    permission_classes = [permissions.IsAuthenticated, IsTeamMember]

    def post(self, request, team_id):
        team = get_object_or_404(Team, pk=team_id, is_active=True)

        membership = get_object_or_404(
            TeamMembership, team=team, user=request.user, is_active=True
        )
        if not membership.can_upload:
            return Response(
                {'error': 'You do not have permission to add files to this team.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = AddTeamFileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file_record = get_object_or_404(
            File,
            pk=serializer.validated_data['file_id'],
            owner=request.user,
            is_trashed=False,
        )

        team_file, created = TeamFile.objects.get_or_create(
            team=team,
            file=file_record,
            defaults={
                'added_by': request.user,
                'folder_path': serializer.validated_data.get('folder_path', ''),
            },
        )

        if not created:
            return Response(
                {'error': 'This file is already shared with the team.'},
                status=status.HTTP_409_CONFLICT,
            )

        team.recalculate_storage()

        return Response(
            TeamFileSerializer(team_file).data,
            status=status.HTTP_201_CREATED,
        )


class RemoveTeamFileView(APIView):
    """Remove a file from a team."""
    permission_classes = [permissions.IsAuthenticated, IsTeamMember]

    def delete(self, request, team_id, team_file_id):
        team_file = get_object_or_404(
            TeamFile, pk=team_file_id, team_id=team_id
        )

        membership = get_object_or_404(
            TeamMembership, team_id=team_id, user=request.user, is_active=True
        )
        if not membership.can_delete and team_file.added_by != request.user:
            return Response(
                {'error': 'You do not have permission to remove this file.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        team_file.delete()
        Team.objects.get(pk=team_id).recalculate_storage()

        return Response(status=status.HTTP_204_NO_CONTENT)


class InviteTeamMemberView(APIView):
    """Send a team invitation."""
    permission_classes = [permissions.IsAuthenticated, IsTeamAdmin]

    def post(self, request, team_id):
        team = get_object_or_404(Team, pk=team_id, is_active=True)

        serializer = CreateTeamInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email'].lower()

        if TeamMembership.objects.filter(
            team=team, user__email=email, is_active=True
        ).exists():
            return Response(
                {'error': 'This user is already a team member.'},
                status=status.HTTP_409_CONFLICT,
            )

        invitation = TeamInvitation.objects.create(
            team=team,
            invited_by=request.user,
            invited_email=email,
            role=serializer.validated_data['role'],
            message=serializer.validated_data.get('message', ''),
            expires_at=timezone.now() + timedelta(days=14),
        )

        return Response(
            TeamInvitationSerializer(invitation).data,
            status=status.HTTP_201_CREATED,
        )


class RespondTeamInvitationView(APIView):
    """Accept or decline a team invitation."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, invitation_id):
        invitation = get_object_or_404(
            TeamInvitation,
            pk=invitation_id,
            invited_email=request.user.email,
            status='pending',
        )

        if invitation.is_expired:
            invitation.status = 'expired'
            invitation.save(update_fields=['status'])
            return Response(
                {'error': 'This invitation has expired.'},
                status=status.HTTP_410_GONE,
            )

        action = request.data.get('action', 'accept').lower()
        if action == 'accept':
            TeamMembership.objects.get_or_create(
                team=invitation.team,
                user=request.user,
                defaults={
                    'role': invitation.role,
                    'invited_by': invitation.invited_by,
                },
            )
            invitation.status = 'accepted'
            invitation.save(update_fields=['status'])

            ActivityLog.log(
                user=request.user,
                action='team_join',
                target_type='team',
                target_id=str(invitation.team.id),
                target_name=invitation.team.name,
            )
        elif action == 'decline':
            invitation.status = 'declined'
            invitation.save(update_fields=['status'])
        else:
            return Response(
                {'error': 'Action must be "accept" or "decline".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(TeamInvitationSerializer(invitation).data)


class LeaveTeamView(APIView):
    """Leave a team."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, team_id):
        membership = get_object_or_404(
            TeamMembership,
            team_id=team_id,
            user=request.user,
            is_active=True,
        )

        if membership.role == 'owner':
            return Response(
                {'error': 'The team owner cannot leave. Transfer ownership or delete the team.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        membership.is_active = False
        membership.save(update_fields=['is_active', 'updated_at'])

        ActivityLog.log(
            user=request.user,
            action='team_leave',
            target_type='team',
            target_id=str(team_id),
            target_name=membership.team.name,
        )

        return Response({'message': f'You have left "{membership.team.name}".'})
