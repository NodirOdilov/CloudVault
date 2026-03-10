from django.contrib import admin

from .models import ShareInvitation, ShareActivity


@admin.register(ShareInvitation)
class ShareInvitationAdmin(admin.ModelAdmin):
    list_display = [
        'invited_email', 'invited_by', 'file', 'folder',
        'permission', 'status', 'expires_at', 'created_at',
    ]
    list_filter = ['status', 'permission', 'created_at']
    search_fields = ['invited_email', 'invited_by__email', 'file__name', 'folder__name']
    readonly_fields = ['id', 'token', 'accepted_at', 'created_at', 'updated_at']
    raw_id_fields = ['invited_by', 'invited_user', 'file', 'folder']

    fieldsets = (
        (None, {
            'fields': ('id', 'invited_by', 'invited_email', 'invited_user'),
        }),
        ('Target', {
            'fields': ('file', 'folder', 'permission', 'message'),
        }),
        ('Status', {
            'fields': ('status', 'token', 'expires_at', 'accepted_at'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )


@admin.register(ShareActivity)
class ShareActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'target_type', 'target_name', 'created_at']
    list_filter = ['action', 'target_type', 'created_at']
    search_fields = ['user__email', 'target_name']
    readonly_fields = [
        'id', 'user', 'action', 'target_type', 'target_id',
        'target_name', 'details', 'ip_address', 'user_agent', 'created_at',
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
