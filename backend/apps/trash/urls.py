from django.urls import path

from . import views

app_name = 'trash'

urlpatterns = [
    path('', views.TrashListView.as_view(), name='trash-list'),
    path('summary/', views.TrashSummaryView.as_view(), name='trash-summary'),
    path('empty/', views.EmptyTrashView.as_view(), name='empty-trash'),
    path('files/<uuid:pk>/restore/', views.RestoreFileView.as_view(), name='restore-file'),
    path('files/<uuid:pk>/delete/', views.PermanentDeleteFileView.as_view(), name='delete-file'),
    path('folders/<uuid:pk>/restore/', views.RestoreFolderView.as_view(), name='restore-folder'),
    path('folders/<uuid:pk>/delete/', views.PermanentDeleteFolderView.as_view(), name='delete-folder'),
]
