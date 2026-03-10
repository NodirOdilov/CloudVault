from django.contrib import admin

from .models import Team, TeamMembership, TeamFile, TeamInvitation


class TeamMembershipInline(admin.TabularInline):
    model = TeamMembership
    extra = 0
    readonly_fields = ['joined_at']
    raw_id_fields = ['user', 'invited_by']


class TeamFileInline(admin.TabularInline):
    model = TeamFile
    extra = 0
    readonly_fields = ['created_at']
    raw_id_fields = ['file', 'added_by']


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'owner', 'member_count', 'storage_used',
        'storage_quota', 'is_active', 'created_at',
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'owner__email', 'description']
    readonly_fields = [
        'id', 'member_count', 'storage_percentage',
        'storage_available', 'created_at', 'updated_at',
    ]
    raw_id_fields = ['owner']
    inlines = [TeamMembershipInline, TeamFileInline]

    def member_count(self, obj):
        return obj.member_count
    member_count.short_description = 'Members'


@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    list_display = ['team', 'user', 'role', 'is_active', 'joined_at']
    list_filter = ['role', 'is_active', 'joined_at']
    search_fields = ['team__name', 'user__email']
    raw_id_fields = ['team', 'user', 'invited_by']


@admin.register(TeamFile)
class TeamFileAdmin(admin.ModelAdmin):
    list_display = ['team', 'file', 'added_by', 'folder_path', 'created_at']
    list_filter = ['created_at']
    search_fields = ['team__name', 'file__name', 'added_by__email']
    raw_id_fields = ['team', 'file', 'added_by']


@admin.register(TeamInvitation)
class TeamInvitationAdmin(admin.ModelAdmin):
    list_display = [
        'team', 'invited_email', 'invited_by', 'role',
        'status', 'expires_at', 'created_at',
    ]
    list_filter = ['status', 'role', 'created_at']
    search_fields = ['team__name', 'invited_email', 'invited_by__email']
    raw_id_fields = ['team', 'invited_by']
