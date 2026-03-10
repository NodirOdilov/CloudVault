from django.utils import timezone
from datetime import timedelta
from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from apps.files.serializers import FileShareSerializer, SharedLinkSerializer
from .models import ShareInvitation, ShareActivity


class ShareInvitationSerializer(serializers.ModelSerializer):
    invited_by = UserSerializer(read_only=True)
    invited_user = UserSerializer(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    is_pending = serializers.BooleanField(read_only=True)
    file_name = serializers.SerializerMethodField()
    folder_name = serializers.SerializerMethodField()

    class Meta:
        model = ShareInvitation
        fields = [
            'id', 'invited_by', 'invited_email', 'invited_user',
            'file', 'file_name', 'folder', 'folder_name',
            'permission', 'message', 'token', 'status',
            'is_expired', 'is_pending', 'expires_at',
            'accepted_at', 'created_at',
        ]
        read_only_fields = [
            'id', 'invited_by', 'invited_user', 'token',
            'status', 'accepted_at', 'created_at',
        ]

    def get_file_name(self, obj):
        return obj.file.name if obj.file else None

    def get_folder_name(self, obj):
        return obj.folder.name if obj.folder else None


class CreateShareInvitationSerializer(serializers.Serializer):
    invited_email = serializers.EmailField()
    file_id = serializers.UUIDField(required=False)
    folder_id = serializers.UUIDField(required=False)
    permission = serializers.ChoiceField(
        choices=['view', 'edit', 'download', 'upload', 'manage'],
        default='view',
    )
    message = serializers.CharField(required=False, allow_blank=True, default='')
    expires_in_days = serializers.IntegerField(
        required=False, default=7, min_value=1, max_value=90,
    )

    def validate(self, attrs):
        if not attrs.get('file_id') and not attrs.get('folder_id'):
            raise serializers.ValidationError(
                'Either file_id or folder_id must be provided.'
            )
        if attrs.get('file_id') and attrs.get('folder_id'):
            raise serializers.ValidationError(
                'Provide either file_id or folder_id, not both.'
            )

        user = self.context['request'].user
        if attrs['invited_email'].lower() == user.email.lower():
            raise serializers.ValidationError(
                {'invited_email': 'You cannot invite yourself.'}
            )

        return attrs


class CreateSharedLinkSerializer(serializers.Serializer):
    file_id = serializers.UUIDField()
    permission = serializers.ChoiceField(
        choices=['view', 'download'],
        default='view',
    )
    password = serializers.CharField(required=False, allow_blank=True, default='')
    expires_in_hours = serializers.IntegerField(
        required=False, allow_null=True, min_value=1, max_value=8760,
    )
    max_downloads = serializers.IntegerField(
        required=False, allow_null=True, min_value=1, max_value=10000,
    )


class SharedLinkAccessSerializer(serializers.Serializer):
    password = serializers.CharField(required=False, allow_blank=True, default='')


class BulkShareSerializer(serializers.Serializer):
    """Share multiple files/folders with multiple users at once."""
    emails = serializers.ListField(
        child=serializers.EmailField(),
        min_length=1,
        max_length=50,
    )
    file_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        default=[],
    )
    folder_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        default=[],
    )
    permission = serializers.ChoiceField(
        choices=['view', 'edit', 'download'],
        default='view',
    )
    message = serializers.CharField(required=False, allow_blank=True, default='')

    def validate(self, attrs):
        if not attrs.get('file_ids') and not attrs.get('folder_ids'):
            raise serializers.ValidationError(
                'At least one file_id or folder_id must be provided.'
            )
        return attrs


class ShareActivitySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ShareActivity
        fields = [
            'id', 'user', 'action', 'target_type', 'target_id',
            'target_name', 'details', 'created_at',
        ]
