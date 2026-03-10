from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from .models import File, FileVersion, FileShare, SharedLink


class FileVersionSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)
    size_display = serializers.SerializerMethodField()

    class Meta:
        model = FileVersion
        fields = [
            'id', 'version_number', 'size', 'size_display', 'checksum',
            'uploaded_by', 'comment', 'created_at',
        ]
        read_only_fields = ['id', 'version_number', 'size', 'checksum', 'created_at']

    def get_size_display(self, obj):
        num = obj.size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if abs(num) < 1024.0:
                return f"{num:.1f} {unit}"
            num /= 1024.0
        return f"{num:.1f} PB"


class FileSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    size_display = serializers.CharField(read_only=True)
    file_type_category = serializers.CharField(read_only=True)
    is_previewable = serializers.BooleanField(read_only=True)
    path = serializers.CharField(read_only=True)
    folder_name = serializers.SerializerMethodField()
    version_count = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = [
            'id', 'owner', 'folder', 'folder_name', 'name', 'original_name',
            'size', 'size_display', 'mime_type', 'extension', 'file_type_category',
            'is_previewable', 'current_version', 'version_count', 'description',
            'tags', 'is_trashed', 'trashed_at', 'is_starred', 'path',
            'created_at', 'updated_at', 'last_accessed_at',
        ]
        read_only_fields = [
            'id', 'owner', 'original_name', 'size', 'mime_type', 'extension',
            'storage_key', 'storage_bucket', 'checksum', 'etag',
            'current_version', 'is_trashed', 'trashed_at',
            'created_at', 'updated_at', 'last_accessed_at',
        ]

    def get_folder_name(self, obj):
        return obj.folder.name if obj.folder else None

    def get_version_count(self, obj):
        return obj.versions.count()


class FileListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for file listings."""
    size_display = serializers.CharField(read_only=True)
    file_type_category = serializers.CharField(read_only=True)
    is_previewable = serializers.BooleanField(read_only=True)
    folder_name = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = [
            'id', 'name', 'size', 'size_display', 'mime_type', 'extension',
            'file_type_category', 'is_previewable', 'is_starred', 'folder',
            'folder_name', 'current_version', 'created_at', 'updated_at',
        ]

    def get_folder_name(self, obj):
        return obj.folder.name if obj.folder else None


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    folder = serializers.UUIDField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True, default='')


class FileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ['name', 'description', 'tags', 'is_starred', 'folder']


class FileVersionUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    comment = serializers.CharField(required=False, allow_blank=True, default='')


class FileShareSerializer(serializers.ModelSerializer):
    shared_by = UserSerializer(read_only=True)
    shared_with = UserSerializer(read_only=True)
    shared_with_email = serializers.EmailField(write_only=True)

    class Meta:
        model = FileShare
        fields = [
            'id', 'file', 'shared_by', 'shared_with', 'shared_with_email',
            'permission', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'shared_by', 'shared_with', 'created_at', 'updated_at']


class SharedLinkSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    is_accessible = serializers.BooleanField(read_only=True)
    file_name = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    class Meta:
        model = SharedLink
        fields = [
            'id', 'file', 'file_name', 'created_by', 'token', 'permission',
            'password', 'expires_at', 'max_downloads', 'download_count',
            'is_active', 'is_expired', 'is_accessible', 'url',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'created_by', 'token', 'download_count',
            'created_at', 'updated_at',
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
        }

    def get_file_name(self, obj):
        return obj.file.name

    def get_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/api/sharing/access/{obj.token}/')
        return f'/api/sharing/access/{obj.token}/'


class FileMoveSerializer(serializers.Serializer):
    destination_folder = serializers.UUIDField(required=False, allow_null=True)


class FileCopySerializer(serializers.Serializer):
    destination_folder = serializers.UUIDField(required=False, allow_null=True)
    new_name = serializers.CharField(required=False, allow_blank=True)
