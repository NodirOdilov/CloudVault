from django.urls import path

from . import views

app_name = 'folders'

urlpatterns = [
    path('', views.FolderListView.as_view(), name='folder-list'),
    path('tree/', views.FolderTreeView.as_view(), name='folder-tree'),
    path('<uuid:pk>/', views.FolderDetailView.as_view(), name='folder-detail'),
    path('<uuid:pk>/contents/', views.FolderContentsView.as_view(), name='folder-contents'),
    path('<uuid:pk>/move/', views.FolderMoveView.as_view(), name='folder-move'),
    path('<uuid:pk>/star/', views.StarFolderView.as_view(), name='folder-star'),
]
