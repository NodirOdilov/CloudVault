import uuid

from django.conf import settings
from django.db import models


class ActivityLog(models.Model):
    """Tracks all user activity across the platform."""
    ACTION_CHOICES = [
        ('upload', 'File Uploaded'),
        ('download', 'File Downloaded'),
        ('delete', 'Permanently Deleted'),
        ('trash', 'Moved to Trash'),
        ('restore', 'Restored from Trash'),
        ('rename', 'Renamed'),
        ('move', 'Moved'),
        ('copy', 'Copied'),
        ('create', 'Created'),
        ('update', 'Updated'),
        ('share', 'Shared'),
        ('unshare', 'Unshared'),
        ('version_upload', 'Version Uploaded'),
        ('version_restore', 'Version Restored'),
        ('star', 'Starred'),
        ('unstar', 'Unstarred'),
        ('login', 'User Logged In'),
        ('logout', 'User Logged Out'),
        ('team_join', 'Joined Team'),
        ('team_leave', 'Left Team'),
    ]

    TARGET_TYPE_CHOICES = [
        ('file', 'File'),
        ('folder', 'Folder'),
        ('share', 'Share'),
        ('link', 'Shared Link'),
        ('team', 'Team'),
        ('user', 'User'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='activity_logs',
    )
    action = models.CharField(max_length=30, choices=ACTION_CHOICES, db_index=True)
    target_type = models.CharField(
        max_length=20,
        choices=TARGET_TYPE_CHOICES,
        db_index=True,
    )
    target_id = models.CharField(max_length=36, blank=True, default='')
    target_name = models.CharField(max_length=500, blank=True, default='')
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'activity_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'action']),
            models.Index(fields=['target_type', 'target_id']),
            models.Index(fields=['-created_at']),
        ]
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'

    def __str__(self):
        return f"{self.user.email} {self.action} {self.target_type}: {self.target_name}"

    @classmethod
    def log(cls, user, action, target_type, target_id='', target_name='',
            details=None, ip_address=None):
        """Create an activity log entry."""
        return cls.objects.create(
            user=user,
            action=action,
            target_type=target_type,
            target_id=str(target_id) if target_id else '',
            target_name=target_name,
            details=details or {},
            ip_address=ip_address,
        )

    @classmethod
    def get_user_activity(cls, user, limit=50, action_filter=None):
        """Get recent activity for a user."""
        queryset = cls.objects.filter(user=user)
        if action_filter:
            queryset = queryset.filter(action=action_filter)
        return queryset[:limit]

    @classmethod
    def get_file_activity(cls, file_id, limit=50):
        """Get activity log for a specific file."""
        return cls.objects.filter(
            target_type='file',
            target_id=str(file_id),
        )[:limit]

    @classmethod
    def get_daily_summary(cls, user, date):
        """Get activity summary for a specific date."""
        from django.db.models import Count
        return cls.objects.filter(
            user=user,
            created_at__date=date,
        ).values('action').annotate(
            count=Count('id')
        ).order_by('-count')
