from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from .models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    type_display = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id', 'sender', 'notification_type', 'type_display',
            'title', 'message', 'priority', 'target_type',
            'target_id', 'action_url', 'is_read', 'read_at',
            'is_archived', 'metadata', 'time_ago', 'created_at',
        ]
        read_only_fields = [
            'id', 'sender', 'notification_type', 'title',
            'message', 'priority', 'target_type', 'target_id',
            'action_url', 'metadata', 'created_at',
        ]

    def get_type_display(self, obj):
        return obj.get_notification_type_display()

    def get_time_ago(self, obj):
        """Generate a human-readable time difference."""
        from django.utils import timezone
        diff = timezone.now() - obj.created_at
        seconds = diff.total_seconds()

        if seconds < 60:
            return 'just now'
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f'{minutes}m ago'
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f'{hours}h ago'
        elif seconds < 604800:
            days = int(seconds / 86400)
            return f'{days}d ago'
        else:
            weeks = int(seconds / 604800)
            return f'{weeks}w ago'


class NotificationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for notification lists."""
    sender_name = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'title', 'priority',
            'is_read', 'sender_name', 'action_url', 'created_at',
        ]

    def get_sender_name(self, obj):
        if obj.sender:
            return obj.sender.full_name or obj.sender.email
        return 'System'


class MarkNotificationsReadSerializer(serializers.Serializer):
    notification_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
    )
    mark_all = serializers.BooleanField(default=False)


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            'email_file_shared', 'email_team_events',
            'email_storage_warnings', 'email_weekly_digest',
            'push_file_shared', 'push_team_events',
            'push_storage_warnings',
            'quiet_hours_start', 'quiet_hours_end',
            'updated_at',
        ]
        read_only_fields = ['updated_at']
