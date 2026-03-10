from django.contrib import admin

from .models import Folder, FolderPermission


@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'owner', 'parent', 'color', 'is_trashed',
        'is_starred', 'file_count', 'created_at',
    ]
    list_filter = ['is_trashed', 'is_starred', 'created_at']
    search_fields = ['name', 'owner__email', 'description']
    readonly_fields = [
        'id', 'path', 'breadcrumb', 'depth', 'total_size',
        'file_count', 'subfolder_count', 'created_at', 'updated_at',
    ]
    raw_id_fields = ['owner', 'parent']

    def file_count(self, obj):
        return obj.file_count
    file_count.short_description = 'Files'


@admin.register(FolderPermission)
class FolderPermissionAdmin(admin.ModelAdmin):
    list_display = ['folder', 'user', 'permission', 'granted_by', 'created_at']
    list_filter = ['permission', 'created_at']
    search_fields = ['folder__name', 'user__email', 'granted_by__email']
    raw_id_fields = ['folder', 'user', 'granted_by']
