from django.contrib import admin

from .models import File, FileVersion, FileShare, SharedLink


class FileVersionInline(admin.TabularInline):
    model = FileVersion
    extra = 0
    readonly_fields = ['version_number', 'storage_key', 'size', 'checksum', 'uploaded_by', 'created_at']


class FileShareInline(admin.TabularInline):
    model = FileShare
    extra = 0
    readonly_fields = ['shared_by', 'created_at']


class SharedLinkInline(admin.TabularInline):
    model = SharedLink
    extra = 0
    readonly_fields = ['token', 'created_by', 'download_count', 'created_at']


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'size_display', 'mime_type', 'folder', 'is_trashed', 'is_starred', 'created_at']
    list_filter = ['is_trashed', 'is_starred', 'mime_type', 'created_at']
    search_fields = ['name', 'owner__email', 'description']
    readonly_fields = [
        'id', 'storage_key', 'storage_bucket', 'checksum', 'etag',
        'current_version', 'created_at', 'updated_at', 'last_accessed_at',
    ]
    inlines = [FileVersionInline, FileShareInline, SharedLinkInline]
    raw_id_fields = ['owner', 'folder']

    def size_display(self, obj):
        return obj.size_display
    size_display.short_description = 'Size'


@admin.register(FileVersion)
class FileVersionAdmin(admin.ModelAdmin):
    list_display = ['file', 'version_number', 'size', 'uploaded_by', 'created_at']
    list_filter = ['created_at']
    search_fields = ['file__name']
    raw_id_fields = ['file', 'uploaded_by']


@admin.register(FileShare)
class FileShareAdmin(admin.ModelAdmin):
    list_display = ['file', 'shared_by', 'shared_with', 'permission', 'created_at']
    list_filter = ['permission', 'created_at']
    search_fields = ['file__name', 'shared_by__email', 'shared_with__email']
    raw_id_fields = ['file', 'shared_by', 'shared_with']


@admin.register(SharedLink)
class SharedLinkAdmin(admin.ModelAdmin):
    list_display = ['file', 'created_by', 'token', 'permission', 'is_active', 'download_count', 'expires_at']
    list_filter = ['is_active', 'permission', 'created_at']
    search_fields = ['file__name', 'token', 'created_by__email']
    readonly_fields = ['token', 'download_count']
    raw_id_fields = ['file', 'created_by']
