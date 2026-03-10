from django.urls import path

from . import views

app_name = 'activity'

urlpatterns = [
    path('', views.ActivityFeedView.as_view(), name='activity-feed'),
    path('recent/', views.RecentActivityView.as_view(), name='recent-activity'),
    path('summary/', views.ActivitySummaryView.as_view(), name='activity-summary'),
    path('<str:target_type>/<uuid:target_id>/', views.ActivityDetailView.as_view(), name='activity-detail'),
]
