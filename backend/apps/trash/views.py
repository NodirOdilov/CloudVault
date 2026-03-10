import logging

from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.activity.models import ActivityLog
from apps.files.models import File
from apps.files.serializers import FileListSerializer
from apps.files.services import FileDeletionService
from apps.folders.models import Folder
from apps.folders.serializers import FolderListSerializer

logger = logging.getLogger(__name__)


class TrashListView(APIView):
    """List all trashed files and folders."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        trashed_files = File.objects.filter(
            owner=request.user,
            is_trashed=True,
        ).order_by('-trashed_at')

        trashed_folders = Folder.objects.filter(
            owner=request.user,
            is_trashed=True,
            parent__is_trashed=False,
        ).order_by('-trashed_at')

        retention_days = settings.TRASH_RETENTION_DAYS

        return Response({
            'files': FileListSerializer(trashed_files, many=True).data,
            'folders': FolderListSerializer(trashed_folders, many=True).data,
            'retention_days': retention_days,
            'total_items': trashed_files.count() + trashed_folders.count(),
        })


class RestoreFileView(APIView):
    """Restore a file from trash."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        file_record = get_object_or_404(
            File, pk=pk, owner=request.user, is_trashed=True
        )

        if file_record.folder and file_record.folder.is_trashed:
            file_record.folder = None

        FileDeletionService.restore(file_record)

        ActivityLog.log(
            user=request.user,
            action='restore',
            target_type='file',
            target_id=str(file_record.id),
            target_name=file_record.name,
        )

        return Response({'message': f'"{file_record.name}" has been restored.'})


class RestoreFolderView(APIView):
    """Restore a folder from trash along with its contents."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        folder = get_object_or_404(
            Folder, pk=pk, owner=request.user, is_trashed=True
        )

        if folder.parent and folder.parent.is_trashed:
            folder.parent = None

        folder.is_trashed = False
        folder.trashed_at = None
        folder.save(update_fields=['is_trashed', 'trashed_at', 'parent', 'updated_at'])

        restored_count = self._restore_descendants(folder)

        ActivityLog.log(
            user=request.user,
            action='restore',
            target_type='folder',
            target_id=str(folder.id),
            target_name=folder.name,
            details={'restored_items': restored_count},
        )

        return Response({
            'message': f'"{folder.name}" and {restored_count} items have been restored.',
        })

    def _restore_descendants(self, folder):
        """Recursively restore all children of a folder."""
        count = 0

        File.objects.filter(folder=folder, is_trashed=True).update(
            is_trashed=False, trashed_at=None
        )
        count += File.objects.filter(folder=folder, is_trashed=False).count()

        for child_folder in Folder.objects.filter(parent=folder, is_trashed=True):
            child_folder.is_trashed = False
            child_folder.trashed_at = None
            child_folder.save(update_fields=['is_trashed', 'trashed_at', 'updated_at'])
            count += 1
            count += self._restore_descendants(child_folder)

        return count


class PermanentDeleteFileView(APIView):
    """Permanently delete a file from trash."""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        file_record = get_object_or_404(
            File, pk=pk, owner=request.user, is_trashed=True
        )

        file_name = file_record.name
        FileDeletionService.hard_delete(file_record)

        ActivityLog.log(
            user=request.user,
            action='delete',
            target_type='file',
            target_id=str(pk),
            target_name=file_name,
        )

        return Response(status=status.HTTP_204_NO_CONTENT)


class PermanentDeleteFolderView(APIView):
    """Permanently delete a folder and all its contents from trash."""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        folder = get_object_or_404(
            Folder, pk=pk, owner=request.user, is_trashed=True
        )

        folder_name = folder.name
        deleted_count = self._delete_descendants(folder, request.user)
        folder.delete()

        ActivityLog.log(
            user=request.user,
            action='delete',
            target_type='folder',
            target_id=str(pk),
            target_name=folder_name,
            details={'deleted_items': deleted_count},
        )

        return Response(status=status.HTTP_204_NO_CONTENT)

    def _delete_descendants(self, folder, user):
        """Recursively delete all contents of a folder."""
        count = 0

        for file_record in File.objects.filter(folder=folder):
            FileDeletionService.hard_delete(file_record)
            count += 1

        for child_folder in Folder.objects.filter(parent=folder):
            count += self._delete_descendants(child_folder, user)
            child_folder.delete()
            count += 1

        return count


class EmptyTrashView(APIView):
    """Permanently delete everything in the user's trash."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        trashed_files = File.objects.filter(
            owner=request.user, is_trashed=True
        )
        trashed_folders = Folder.objects.filter(
            owner=request.user, is_trashed=True
        )

        file_count = trashed_files.count()
        folder_count = trashed_folders.count()

        for file_record in trashed_files:
            FileDeletionService.hard_delete(file_record)

        trashed_folders.delete()

        ActivityLog.log(
            user=request.user,
            action='delete',
            target_type='folder',
            target_name='Trash (emptied)',
            details={
                'files_deleted': file_count,
                'folders_deleted': folder_count,
            },
        )

        return Response({
            'message': 'Trash has been emptied.',
            'files_deleted': file_count,
            'folders_deleted': folder_count,
        })


class TrashSummaryView(APIView):
    """Get summary of trash contents."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from django.db.models import Sum

        trashed_files = File.objects.filter(
            owner=request.user, is_trashed=True
        )
        total_size = trashed_files.aggregate(
            total=Sum('size')
        )['total'] or 0

        trashed_folders = Folder.objects.filter(
            owner=request.user, is_trashed=True
        )

        auto_delete_date = None
        oldest_trashed = trashed_files.order_by('trashed_at').first()
        if oldest_trashed and oldest_trashed.trashed_at:
            from datetime import timedelta
            auto_delete_date = (
                oldest_trashed.trashed_at + timedelta(days=settings.TRASH_RETENTION_DAYS)
            ).isoformat()

        return Response({
            'file_count': trashed_files.count(),
            'folder_count': trashed_folders.count(),
            'total_size': total_size,
            'total_size_display': self._format_bytes(total_size),
            'retention_days': settings.TRASH_RETENTION_DAYS,
            'next_auto_delete': auto_delete_date,
        })

    @staticmethod
    def _format_bytes(num_bytes):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if abs(num_bytes) < 1024.0:
                return f"{num_bytes:.1f} {unit}"
            num_bytes /= 1024.0
        return f"{num_bytes:.1f} PB"
