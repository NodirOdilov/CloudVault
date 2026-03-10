from django.contrib import admin

from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'target_type', 'target_name', 'created_at']
    list_filter = ['action', 'target_type', 'created_at']
    search_fields = ['user__email', 'target_name', 'target_id']
    readonly_fields = [
        'id', 'user', 'action', 'target_type', 'target_id',
        'target_name', 'details', 'ip_address', 'created_at',
    ]
    date_hierarchy = 'created_at'

    fieldsets = (
        (None, {
            'fields': ('id', 'user', 'action'),
        }),
        ('Target', {
            'fields': ('target_type', 'target_id', 'target_name'),
        }),
        ('Details', {
            'fields': ('details', 'ip_address'),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
