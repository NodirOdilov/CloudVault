import uuid

from django.conf import settings
from django.db import models


class Notification(models.Model):
    """User notifications for sharing, team events, and system alerts."""
    TYPE_CHOICES = [
        ('file_shared', 'File Shared'),
        ('folder_shared', 'Folder Shared'),
        ('share_invitation', 'Share Invitation'),
        ('share_accepted', 'Share Accepted'),
        ('team_invitation', 'Team Invitation'),
        ('team_joined', 'Team Joined'),
        ('team_removed', 'Removed from Team'),
        ('file_comment', 'File Comment'),
        ('storage_warning', 'Storage Warning'),
        ('storage_full', 'Storage Full'),
        ('trash_reminder', 'Trash Reminder'),
        ('system', 'System Notification'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_notifications',
    )
    notification_type = models.CharField(
        max_length=30,
        choices=TYPE_CHOICES,
        db_index=True,
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='normal',
    )

    # Link to the relevant resource
    target_type = models.CharField(max_length=30, blank=True, default='')
    target_id = models.UUIDField(null=True, blank=True)
    action_url = models.CharField(max_length=500, blank=True, default='')

    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    is_archived = models.BooleanField(default=False)

    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read', '-created_at']),
            models.Index(fields=['recipient', 'notification_type']),
            models.Index(fields=['-created_at']),
        ]
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        return f"[{self.notification_type}] {self.title} -> {self.recipient.email}"

    def mark_read(self):
        if not self.is_read:
            from django.utils import timezone
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    def archive(self):
        self.is_archived = True
        self.save(update_fields=['is_archived'])

    @classmethod
    def create_notification(cls, recipient, notification_type, title, message,
                            sender=None, target_type='', target_id=None,
                            action_url='', priority='normal', metadata=None):
        """Factory method to create notifications."""
        return cls.objects.create(
            recipient=recipient,
            sender=sender,
            notification_type=notification_type,
            title=title,
            message=message,
            priority=priority,
            target_type=target_type,
            target_id=target_id,
            action_url=action_url,
            metadata=metadata or {},
        )

    @classmethod
    def notify_file_shared(cls, owner, shared_with, file_record, permission):
        """Create a notification when a file is shared."""
        return cls.create_notification(
            recipient=shared_with,
            sender=owner,
            notification_type='file_shared',
            title=f'{owner.full_name} shared a file with you',
            message=f'"{file_record.name}" has been shared with you ({permission} access).',
            target_type='file',
            target_id=file_record.id,
            action_url=f'/files/{file_record.id}',
            metadata={'permission': permission, 'file_name': file_record.name},
        )

    @classmethod
    def notify_team_invitation(cls, invitation):
        """Create a notification for a team invitation."""
        from apps.accounts.models import User
        try:
            recipient = User.objects.get(email=invitation.invited_email)
        except User.DoesNotExist:
            return None

        return cls.create_notification(
            recipient=recipient,
            sender=invitation.invited_by,
            notification_type='team_invitation',
            title=f'You are invited to join "{invitation.team.name}"',
            message=f'{invitation.invited_by.full_name} has invited you to join the team as {invitation.role}.',
            target_type='team',
            target_id=invitation.team.id,
            action_url=f'/teams/invitations/{invitation.id}',
            priority='high',
            metadata={
                'team_name': invitation.team.name,
                'role': invitation.role,
            },
        )

    @classmethod
    def notify_storage_warning(cls, user, usage_percentage):
        """Warn user about storage approaching quota."""
        level = 'urgent' if usage_percentage >= 95 else 'high'
        return cls.create_notification(
            recipient=user,
            notification_type='storage_warning',
            title='Storage space running low',
            message=f'You are using {usage_percentage:.1f}% of your storage quota. Consider freeing up space or upgrading your plan.',
            priority=level,
            action_url='/settings/storage',
            metadata={'usage_percentage': usage_percentage},
        )

    @classmethod
    def get_unread_count(cls, user):
        """Get count of unread notifications for a user."""
        return cls.objects.filter(
            recipient=user, is_read=False, is_archived=False
        ).count()


class NotificationPreference(models.Model):
    """User preferences for notification delivery."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
    )
    email_file_shared = models.BooleanField(default=True)
    email_team_events = models.BooleanField(default=True)
    email_storage_warnings = models.BooleanField(default=True)
    email_weekly_digest = models.BooleanField(default=True)

    push_file_shared = models.BooleanField(default=True)
    push_team_events = models.BooleanField(default=True)
    push_storage_warnings = models.BooleanField(default=True)

    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notification_preferences'
        verbose_name = 'Notification Preference'
        verbose_name_plural = 'Notification Preferences'

    def __str__(self):
        return f"Notification preferences for {self.user.email}"
