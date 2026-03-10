from django.contrib import admin

from .models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'recipient', 'notification_type', 'priority',
        'is_read', 'is_archived', 'created_at',
    ]
    list_filter = [
        'notification_type', 'priority', 'is_read',
        'is_archived', 'created_at',
    ]
    search_fields = ['title', 'message', 'recipient__email', 'sender__email']
    readonly_fields = [
        'id', 'recipient', 'sender', 'notification_type',
        'title', 'message', 'priority', 'target_type',
        'target_id', 'action_url', 'metadata', 'read_at', 'created_at',
    ]
    raw_id_fields = ['recipient', 'sender']
    date_hierarchy = 'created_at'

    fieldsets = (
        (None, {
            'fields': ('id', 'recipient', 'sender', 'notification_type'),
        }),
        ('Content', {
            'fields': ('title', 'message', 'priority'),
        }),
        ('Target', {
            'fields': ('target_type', 'target_id', 'action_url'),
        }),
        ('Status', {
            'fields': ('is_read', 'read_at', 'is_archived'),
        }),
        ('Extra', {
            'fields': ('metadata', 'created_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'email_file_shared', 'email_team_events',
        'email_storage_warnings', 'push_file_shared',
    ]
    search_fields = ['user__email']
    raw_id_fields = ['user']
