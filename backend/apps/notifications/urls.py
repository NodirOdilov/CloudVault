from django.urls import path

from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='notification-list'),
    path('unread-count/', views.UnreadCountView.as_view(), name='unread-count'),
    path('mark-read/', views.MarkReadView.as_view(), name='mark-read'),
    path('clear-all/', views.ClearAllNotificationsView.as_view(), name='clear-all'),
    path('preferences/', views.NotificationPreferenceView.as_view(), name='preferences'),
    path('<uuid:pk>/', views.NotificationDetailView.as_view(), name='notification-detail'),
    path('<uuid:pk>/archive/', views.ArchiveNotificationView.as_view(), name='archive-notification'),
]
