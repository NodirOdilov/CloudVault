from django.urls import path

from . import views

app_name = 'teams'

urlpatterns = [
    path('', views.TeamListView.as_view(), name='team-list'),
    path('<uuid:pk>/', views.TeamDetailView.as_view(), name='team-detail'),
    path('<uuid:team_id>/members/', views.TeamMemberListView.as_view(), name='team-members'),
    path('<uuid:team_id>/members/<uuid:membership_id>/', views.TeamMemberUpdateView.as_view(), name='team-member-update'),
    path('<uuid:team_id>/files/', views.TeamFileListView.as_view(), name='team-files'),
    path('<uuid:team_id>/files/add/', views.AddTeamFileView.as_view(), name='add-team-file'),
    path('<uuid:team_id>/files/<uuid:team_file_id>/remove/', views.RemoveTeamFileView.as_view(), name='remove-team-file'),
    path('<uuid:team_id>/invite/', views.InviteTeamMemberView.as_view(), name='invite-member'),
    path('<uuid:team_id>/leave/', views.LeaveTeamView.as_view(), name='leave-team'),
    path('invitations/<uuid:invitation_id>/respond/', views.RespondTeamInvitationView.as_view(), name='respond-invitation'),
]
