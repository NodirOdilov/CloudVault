from django.urls import path

from . import views

app_name = 'files'

urlpatterns = [
    path('', views.FileListView.as_view(), name='file-list'),
    path('upload/', views.FileUploadView.as_view(), name='file-upload'),
    path('recent/', views.RecentFilesView.as_view(), name='recent-files'),
    path('<uuid:pk>/', views.FileDetailView.as_view(), name='file-detail'),
    path('<uuid:pk>/download/', views.FileDownloadView.as_view(), name='file-download'),
    path('<uuid:pk>/preview/', views.FilePreviewView.as_view(), name='file-preview'),
    path('<uuid:pk>/move/', views.FileMoveView.as_view(), name='file-move'),
    path('<uuid:pk>/copy/', views.FileCopyView.as_view(), name='file-copy'),
    path('<uuid:pk>/star/', views.StarFileView.as_view(), name='file-star'),
    path('<uuid:pk>/versions/', views.FileVersionListView.as_view(), name='file-versions'),
    path('<uuid:pk>/versions/upload/', views.FileVersionUploadView.as_view(), name='file-version-upload'),
    path('<uuid:pk>/versions/<int:version_number>/restore/', views.FileVersionRestoreView.as_view(), name='file-version-restore'),
]
