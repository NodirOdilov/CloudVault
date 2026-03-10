import secrets
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class ShareInvitation(models.Model):
    """Pending share invitations sent to users who may not have accounts yet."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_invitations',
    )
    invited_email = models.EmailField()
    invited_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='received_invitations',
    )
    file = models.ForeignKey(
        'files.File',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='invitations',
    )
    folder = models.ForeignKey(
        'folders.Folder',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='invitations',
    )
    permission = models.CharField(max_length=20, default='view')
    message = models.TextField(blank=True, default='')
    token = models.CharField(
        max_length=64,
        unique=True,
        default=lambda: secrets.token_urlsafe(32),
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
    )
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'share_invitations'
        ordering = ['-created_at']
        verbose_name = 'Share Invitation'
        verbose_name_plural = 'Share Invitations'

    def __str__(self):
        target = self.file.name if self.file else self.folder.name if self.folder else 'Unknown'
        return f"Invite for {target} -> {self.invited_email} ({self.status})"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_pending(self):
        return self.status == 'pending' and not self.is_expired

    def accept(self, user):
        """Accept the invitation and create the appropriate share."""
        from apps.files.models import FileShare

        self.status = 'accepted'
        self.accepted_at = timezone.now()
        self.invited_user = user
        self.save(update_fields=['status', 'accepted_at', 'invited_user', 'updated_at'])

        if self.file:
            FileShare.objects.get_or_create(
                file=self.file,
                shared_with=user,
                defaults={
                    'shared_by': self.invited_by,
                    'permission': self.permission,
                },
            )
        elif self.folder:
            from apps.folders.models import FolderPermission
            FolderPermission.objects.get_or_create(
                folder=self.folder,
                user=user,
                defaults={
                    'permission': self.permission,
                    'granted_by': self.invited_by,
                },
            )

    def decline(self):
        self.status = 'declined'
        self.save(update_fields=['status', 'updated_at'])


class ShareActivity(models.Model):
    """Tracks sharing-related activity for auditing."""
    ACTION_CHOICES = [
        ('share_created', 'Share Created'),
        ('share_updated', 'Share Updated'),
        ('share_revoked', 'Share Revoked'),
        ('link_created', 'Link Created'),
        ('link_accessed', 'Link Accessed'),
        ('link_downloaded', 'Link Downloaded'),
        ('link_deactivated', 'Link Deactivated'),
        ('invitation_sent', 'Invitation Sent'),
        ('invitation_accepted', 'Invitation Accepted'),
        ('invitation_declined', 'Invitation Declined'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='share_activities',
    )
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    target_type = models.CharField(max_length=20)
    target_id = models.UUIDField()
    target_name = models.CharField(max_length=500)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'share_activities'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'action']),
            models.Index(fields=['target_type', 'target_id']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = 'Share Activity'
        verbose_name_plural = 'Share Activities'

    def __str__(self):
        return f"{self.user.email} - {self.action} - {self.target_name}"

    @classmethod
    def log(cls, user, action, target_type, target_id, target_name,
            details=None, request=None):
        ip_address = None
        user_agent = ''
        if request:
            ip_address = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
            if not ip_address:
                ip_address = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

        return cls.objects.create(
            user=user,
            action=action,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )
