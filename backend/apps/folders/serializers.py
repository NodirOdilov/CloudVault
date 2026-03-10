from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from .models import Folder, FolderPermission


class FolderSerializer(serializers.ModelSerializer):
    """Full folder serializer with computed properties."""
    owner = UserSerializer(read_only=True)
    path = serializers.CharField(read_only=True)
    breadcrumb = serializers.ListField(read_only=True)
    depth = serializers.IntegerField(read_only=True)
    total_size = serializers.IntegerField(read_only=True)
    file_count = serializers.IntegerField(read_only=True)
    subfolder_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Folder
        fields = [
            'id', 'owner', 'parent', 'name', 'color', 'description',
            'path', 'breadcrumb', 'depth', 'total_size', 'file_count',
            'subfolder_count', 'is_trashed', 'trashed_at', 'is_starred',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'owner', 'is_trashed', 'trashed_at',
            'created_at', 'updated_at',
        ]


class FolderListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for folder listings."""
    file_count = serializers.IntegerField(read_only=True)
    subfolder_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Folder
        fields = [
            'id', 'parent', 'name', 'color', 'is_starred',
            'file_count', 'subfolder_count', 'created_at', 'updated_at',
        ]


class FolderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        fields = ['name', 'parent', 'color', 'description']

    def validate_name(self, value):
        if '/' in value or '\\' in value:
            raise serializers.ValidationError(
                "Folder name cannot contain '/' or '\\'."
            )
        return value.strip()

    def validate(self, attrs):
        user = self.context['request'].user
        parent = attrs.get('parent')
        name = attrs.get('name')

        if parent and parent.owner != user:
            raise serializers.ValidationError(
                {'parent': 'You do not own the parent folder.'}
            )

        if parent and parent.depth >= 10:
            raise serializers.ValidationError(
                {'parent': 'Maximum folder nesting depth of 10 reached.'}
            )

        exists = Folder.objects.filter(
            owner=user, parent=parent, name=name, is_trashed=False
        ).exists()
        if exists:
            raise serializers.ValidationError(
                {'name': 'A folder with this name already exists here.'}
            )

        return attrs


class FolderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        fields = ['name', 'color', 'description', 'is_starred']


class FolderMoveSerializer(serializers.Serializer):
    destination_parent = serializers.UUIDField(required=False, allow_null=True)

    def validate_destination_parent(self, value):
        if value is None:
            return None
        try:
            folder = Folder.objects.get(id=value)
        except Folder.DoesNotExist:
            raise serializers.ValidationError('Destination folder not found.')
        return value


class FolderPermissionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    granted_by = UserSerializer(read_only=True)
    user_email = serializers.EmailField(write_only=True)

    class Meta:
        model = FolderPermission
        fields = [
            'id', 'folder', 'user', 'user_email', 'permission',
            'granted_by', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'user', 'granted_by', 'created_at', 'updated_at']


class FolderTreeSerializer(serializers.ModelSerializer):
    """Recursive folder tree serializer."""
    children = serializers.SerializerMethodField()
    file_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Folder
        fields = ['id', 'name', 'color', 'children', 'file_count']

    def get_children(self, obj):
        children = obj.children.filter(is_trashed=False).order_by('name')
        return FolderTreeSerializer(children, many=True).data
