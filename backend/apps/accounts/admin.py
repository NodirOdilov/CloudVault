from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, StorageQuota


class StorageQuotaInline(admin.StackedInline):
    model = StorageQuota
    can_delete = False
    verbose_name_plural = 'Storage Quota'
    readonly_fields = ['used_bytes', 'last_calculated']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'full_name', 'is_active', 'is_staff', 'created_at']
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'created_at']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-created_at']
    inlines = [StorageQuotaInline]

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('avatar',)}),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('email', 'first_name', 'last_name')}),
    )


@admin.register(StorageQuota)
class StorageQuotaAdmin(admin.ModelAdmin):
    list_display = ['user', 'quota_bytes', 'used_bytes', 'usage_percentage', 'last_calculated']
    list_filter = ['last_calculated']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['used_bytes', 'last_calculated', 'usage_percentage', 'available_bytes']

    def usage_percentage(self, obj):
        return f"{obj.usage_percentage:.1f}%"
    usage_percentage.short_description = 'Usage'

    def available_bytes(self, obj):
        return obj.available_bytes
    available_bytes.short_description = 'Available (bytes)'
