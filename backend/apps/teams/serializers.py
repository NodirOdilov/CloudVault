from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from .models import Team, TeamMembership, TeamFile, TeamInvitation


class TeamSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    member_count = serializers.IntegerField(read_only=True)
    storage_percentage = serializers.FloatField(read_only=True)
    storage_available = serializers.IntegerField(read_only=True)
    my_role = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = [
            'id', 'name', 'description', 'avatar', 'owner',
            'member_count', 'storage_quota', 'storage_used',
            'storage_percentage', 'storage_available', 'my_role',
            'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'owner', 'storage_used', 'created_at', 'updated_at',
        ]

    def get_my_role(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.get_member_role(request.user)
        return None


class TeamCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['name', 'description', 'avatar']

    def validate_name(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError(
                'Team name must be at least 2 characters.'
            )
        return value.strip()


class TeamUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['name', 'description', 'avatar', 'storage_quota']


class TeamMembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    invited_by = UserSerializer(read_only=True)
    can_upload = serializers.BooleanField(read_only=True)
    can_delete = serializers.BooleanField(read_only=True)
    can_manage_members = serializers.BooleanField(read_only=True)

    class Meta:
        model = TeamMembership
        fields = [
            'id', 'team', 'user', 'role', 'invited_by',
            'can_upload', 'can_delete', 'can_manage_members',
            'is_active', 'joined_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'team', 'user', 'invited_by', 'joined_at', 'updated_at',
        ]


class TeamMemberUpdateSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=['admin', 'editor', 'viewer'])


class TeamFileSerializer(serializers.ModelSerializer):
    added_by = UserSerializer(read_only=True)
    file_name = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()
    file_type = serializers.SerializerMethodField()

    class Meta:
        model = TeamFile
        fields = [
            'id', 'team', 'file', 'file_name', 'file_size',
            'file_type', 'added_by', 'folder_path', 'created_at',
        ]
        read_only_fields = ['id', 'added_by', 'created_at']

    def get_file_name(self, obj):
        return obj.file.name

    def get_file_size(self, obj):
        return obj.file.size

    def get_file_type(self, obj):
        return obj.file.file_type_category


class AddTeamFileSerializer(serializers.Serializer):
    file_id = serializers.UUIDField()
    folder_path = serializers.CharField(required=False, allow_blank=True, default='')


class TeamInvitationSerializer(serializers.ModelSerializer):
    invited_by = UserSerializer(read_only=True)
    team = TeamSerializer(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = TeamInvitation
        fields = [
            'id', 'team', 'invited_by', 'invited_email', 'role',
            'message', 'status', 'is_expired', 'expires_at', 'created_at',
        ]
        read_only_fields = ['id', 'invited_by', 'status', 'created_at']


class CreateTeamInvitationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(
        choices=['admin', 'editor', 'viewer'],
        default='viewer',
    )
    message = serializers.CharField(required=False, allow_blank=True, default='')
