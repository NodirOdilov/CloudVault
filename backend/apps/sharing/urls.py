from django.urls import path

from . import views

app_name = 'sharing'

urlpatterns = [
    # Direct file sharing
    path('files/<uuid:file_id>/share/', views.ShareFileView.as_view(), name='share-file'),
    path('files/<uuid:file_id>/shares/', views.FileSharesListView.as_view(), name='file-shares-list'),
    path('shares/<uuid:share_id>/revoke/', views.RevokeFileShareView.as_view(), name='revoke-share'),

    # Shared with/by me
    path('shared-with-me/', views.SharedWithMeView.as_view(), name='shared-with-me'),
    path('shared-by-me/', views.SharedByMeView.as_view(), name='shared-by-me'),

    # Shared links
    path('links/', views.CreateSharedLinkView.as_view(), name='create-shared-link'),
    path('links/<uuid:pk>/', views.SharedLinkDetailView.as_view(), name='shared-link-detail'),
    path('access/<str:token>/', views.SharedLinkAccessView.as_view(), name='shared-link-access'),

    # Invitations
    path('invitations/', views.InvitationListView.as_view(), name='invitation-list'),
    path('invitations/send/', views.SendInvitationView.as_view(), name='send-invitation'),
    path('invitations/<uuid:pk>/respond/', views.InvitationResponseView.as_view(), name='invitation-respond'),

    # Activity
    path('activity/', views.ShareActivityListView.as_view(), name='share-activity'),
]
