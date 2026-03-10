from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from .models import ActivityLog


class ActivityLogSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    action_display = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    class Meta:
        model = ActivityLog
        fields = [
            'id', 'user', 'action', 'action_display', 'target_type',
            'target_id', 'target_name', 'details', 'description',
            'ip_address', 'created_at',
        ]

    def get_action_display(self, obj):
        return obj.get_action_display()

    def get_description(self, obj):
        """Generate a human-readable activity description."""
        user_name = obj.user.full_name or obj.user.email
        target = obj.target_name or obj.target_type

        descriptions = {
            'upload': f'{user_name} uploaded "{target}"',
            'download': f'{user_name} downloaded "{target}"',
            'delete': f'{user_name} permanently deleted "{target}"',
            'trash': f'{user_name} moved "{target}" to trash',
            'restore': f'{user_name} restored "{target}" from trash',
            'rename': f'{user_name} renamed to "{target}"',
            'move': f'{user_name} moved "{target}"',
            'copy': f'{user_name} copied "{target}"',
            'create': f'{user_name} created {obj.target_type} "{target}"',
            'update': f'{user_name} updated "{target}"',
            'share': f'{user_name} shared "{target}"',
            'unshare': f'{user_name} removed sharing for "{target}"',
            'version_upload': f'{user_name} uploaded a new version of "{target}"',
            'version_restore': f'{user_name} restored a version of "{target}"',
            'star': f'{user_name} starred "{target}"',
            'unstar': f'{user_name} unstarred "{target}"',
        }

        description = descriptions.get(obj.action, f'{user_name} performed {obj.action} on "{target}"')

        if obj.action == 'rename' and obj.details.get('old_name'):
            description = f'{user_name} renamed "{obj.details["old_name"]}" to "{target}"'
        elif obj.action == 'move' and obj.details.get('from') and obj.details.get('to'):
            description += f' from "{obj.details["from"]}" to "{obj.details["to"]}"'

        return description


class ActivityLogListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for activity feed."""
    action_display = serializers.SerializerMethodField()

    class Meta:
        model = ActivityLog
        fields = [
            'id', 'action', 'action_display', 'target_type',
            'target_id', 'target_name', 'created_at',
        ]

    def get_action_display(self, obj):
        return obj.get_action_display()


class ActivitySummarySerializer(serializers.Serializer):
    action = serializers.CharField()
    count = serializers.IntegerField()
    action_display = serializers.SerializerMethodField()

    def get_action_display(self, obj):
        action_labels = dict(ActivityLog.ACTION_CHOICES)
        return action_labels.get(obj['action'], obj['action'])
