import uuid

from django.conf import settings
from django.db import models


class Team(models.Model):
    """Represents a team/workspace for collaborative file management."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    avatar = models.URLField(max_length=500, blank=True, default='')
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_teams',
    )
    storage_quota = models.BigIntegerField(
        default=53687091200,  # 50 GB
        help_text='Team storage quota in bytes',
    )
    storage_used = models.BigIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'teams'
        ordering = ['name']
        verbose_name = 'Team'
        verbose_name_plural = 'Teams'

    def __str__(self):
        return self.name

    @property
    def member_count(self):
        return self.memberships.filter(is_active=True).count()

    @property
    def storage_percentage(self):
        if self.storage_quota == 0:
            return 100.0
        return (self.storage_used / self.storage_quota) * 100

    @property
    def storage_available(self):
        return max(0, self.storage_quota - self.storage_used)

    def has_member(self, user):
        return self.memberships.filter(user=user, is_active=True).exists()

    def get_member_role(self, user):
        try:
            membership = self.memberships.get(user=user, is_active=True)
            return membership.role
        except TeamMembership.DoesNotExist:
            return None

    def recalculate_storage(self):
        """Recalculate team storage usage from team files."""
        total = TeamFile.objects.filter(
            team=self
        ).aggregate(total=models.Sum('file__size'))['total'] or 0
        self.storage_used = total
        self.save(update_fields=['storage_used', 'updated_at'])
        return total


class TeamMembership(models.Model):
    """Team membership with role-based access."""
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('editor', 'Editor'),
        ('viewer', 'Viewer'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='memberships',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='team_memberships',
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='viewer')
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='team_invitations_sent',
    )
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'team_memberships'
        unique_together = ['team', 'user']
        ordering = ['role', 'joined_at']
        verbose_name = 'Team Membership'
        verbose_name_plural = 'Team Memberships'

    def __str__(self):
        return f"{self.user.email} - {self.team.name} ({self.role})"

    @property
    def can_upload(self):
        return self.role in ('owner', 'admin', 'editor')

    @property
    def can_delete(self):
        return self.role in ('owner', 'admin')

    @property
    def can_manage_members(self):
        return self.role in ('owner', 'admin')

    @property
    def can_edit_team(self):
        return self.role in ('owner', 'admin')


class TeamFile(models.Model):
    """Association between teams and shared files."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='team_files',
    )
    file = models.ForeignKey(
        'files.File',
        on_delete=models.CASCADE,
        related_name='team_associations',
    )
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='team_files_added',
    )
    folder_path = models.CharField(
        max_length=1000,
        blank=True,
        default='',
        help_text='Virtual folder path within the team',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'team_files'
        unique_together = ['team', 'file']
        ordering = ['-created_at']
        verbose_name = 'Team File'
        verbose_name_plural = 'Team Files'

    def __str__(self):
        return f"{self.file.name} in {self.team.name}"


class TeamInvitation(models.Model):
    """Pending team invitations."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='invitations',
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='team_invite_sent',
    )
    invited_email = models.EmailField()
    role = models.CharField(max_length=20, default='viewer')
    message = models.TextField(blank=True, default='')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
    )
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'team_invitations'
        ordering = ['-created_at']
        verbose_name = 'Team Invitation'
        verbose_name_plural = 'Team Invitations'

    def __str__(self):
        return f"Invite to {self.team.name} for {self.invited_email}"

    @property
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at
