import logging

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.activity.models import ActivityLog
from .models import File, FileVersion
from .serializers import (
    FileSerializer,
    FileListSerializer,
    FileUploadSerializer,
    FileUpdateSerializer,
    FileVersionSerializer,
    FileVersionUploadSerializer,
    FileMoveSerializer,
    FileCopySerializer,
)
from .services import (
    FileUploadService,
    FileDownloadService,
    FileVersionService,
    FilePreviewService,
    FileDeletionService,
)

logger = logging.getLogger(__name__)


class FileListView(generics.ListAPIView):
    """List files for the authenticated user."""
    serializer_class = FileListSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'description', 'tags']
    ordering_fields = ['name', 'size', 'created_at', 'updated_at', 'mime_type']
    ordering = ['-updated_at']

    def get_queryset(self):
        queryset = File.objects.filter(
            owner=self.request.user,
            is_trashed=False,
        ).select_related('folder')

        folder_id = self.request.query_params.get('folder')
        if folder_id:
            queryset = queryset.filter(folder_id=folder_id)
        elif self.request.query_params.get('root') == 'true':
            queryset = queryset.filter(folder__isnull=True)

        file_type = self.request.query_params.get('type')
        if file_type:
            type_mapping = {
                'image': ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml'],
                'document': ['application/pdf', 'application/msword',
                             'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
                'video': ['video/mp4', 'video/webm', 'video/ogg'],
                'audio': ['audio/mpeg', 'audio/wav', 'audio/ogg'],
                'archive': ['application/zip', 'application/x-rar-compressed', 'application/gzip'],
            }
            mime_types = type_mapping.get(file_type, [])
            if mime_types:
                queryset = queryset.filter(mime_type__in=mime_types)

        starred = self.request.query_params.get('starred')
        if starred == 'true':
            queryset = queryset.filter(is_starred=True)

        return queryset


class FileUploadView(APIView):
    """Upload a new file."""
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file_obj = serializer.validated_data['file']
        folder_id = serializer.validated_data.get('folder')
        description = serializer.validated_data.get('description', '')

        folder = None
        if folder_id:
            from apps.folders.models import Folder
            folder = get_object_or_404(Folder, id=folder_id, owner=request.user)

        file_record = FileUploadService.upload_file(
            user=request.user,
            file_obj=file_obj,
            folder=folder,
            description=description,
        )

        ActivityLog.log(
            user=request.user,
            action='upload',
            target_type='file',
            target_id=str(file_record.id),
            target_name=file_record.name,
            details={'size': file_record.size, 'mime_type': file_record.mime_type},
        )

        return Response(
            FileSerializer(file_record).data,
            status=status.HTTP_201_CREATED,
        )


class FileDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a specific file."""
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return FileUpdateSerializer
        return FileSerializer

    def get_queryset(self):
        return File.objects.filter(owner=self.request.user)

    def perform_update(self, serializer):
        old_name = self.get_object().name
        instance = serializer.save()
        if instance.name != old_name:
            ActivityLog.log(
                user=self.request.user,
                action='rename',
                target_type='file',
                target_id=str(instance.id),
                target_name=instance.name,
                details={'old_name': old_name},
            )

    def perform_destroy(self, instance):
        FileDeletionService.soft_delete(instance)
        ActivityLog.log(
            user=self.request.user,
            action='trash',
            target_type='file',
            target_id=str(instance.id),
            target_name=instance.name,
        )


class FileDownloadView(APIView):
    """Generate a download URL for a file."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        file_record = get_object_or_404(File, pk=pk, owner=request.user, is_trashed=False)

        download_url = FileDownloadService.get_download_url(file_record)
        FileDownloadService.record_access(file_record)

        ActivityLog.log(
            user=request.user,
            action='download',
            target_type='file',
            target_id=str(file_record.id),
            target_name=file_record.name,
        )

        return Response({
            'download_url': download_url,
            'file_name': file_record.name,
            'mime_type': file_record.mime_type,
            'size': file_record.size,
        })


class FilePreviewView(APIView):
    """Get preview data for a file."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        file_record = get_object_or_404(File, pk=pk, owner=request.user, is_trashed=False)

        if file_record.file_type_category == 'text':
            preview = FilePreviewService.get_text_preview(file_record)
        else:
            preview = FilePreviewService.get_preview_url(file_record)

        if preview is None:
            return Response(
                {'message': 'Preview not available for this file type.'},
                status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )

        return Response(preview)


class FileVersionListView(generics.ListAPIView):
    """List all versions of a file."""
    serializer_class = FileVersionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        file_record = get_object_or_404(
            File, pk=self.kwargs['pk'], owner=self.request.user
        )
        return FileVersionService.get_versions(file_record)


class FileVersionUploadView(APIView):
    """Upload a new version of an existing file."""
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        file_record = get_object_or_404(File, pk=pk, owner=request.user, is_trashed=False)

        serializer = FileVersionUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file_obj = serializer.validated_data['file']
        comment = serializer.validated_data.get('comment', '')

        version = FileUploadService.upload_new_version(
            user=request.user,
            file_record=file_record,
            file_obj=file_obj,
            comment=comment,
        )

        ActivityLog.log(
            user=request.user,
            action='version_upload',
            target_type='file',
            target_id=str(file_record.id),
            target_name=file_record.name,
            details={'version': version.version_number},
        )

        return Response(
            FileVersionSerializer(version).data,
            status=status.HTTP_201_CREATED,
        )


class FileVersionRestoreView(APIView):
    """Restore a file to a specific version."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, version_number):
        file_record = get_object_or_404(File, pk=pk, owner=request.user, is_trashed=False)

        file_record = FileVersionService.restore_version(
            file_record=file_record,
            version_number=version_number,
            user=request.user,
        )

        ActivityLog.log(
            user=request.user,
            action='version_restore',
            target_type='file',
            target_id=str(file_record.id),
            target_name=file_record.name,
            details={'restored_version': version_number},
        )

        return Response(FileSerializer(file_record).data)


class FileMoveView(APIView):
    """Move a file to a different folder."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        file_record = get_object_or_404(File, pk=pk, owner=request.user, is_trashed=False)

        serializer = FileMoveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dest_folder_id = serializer.validated_data.get('destination_folder')
        old_folder_name = file_record.folder.name if file_record.folder else 'Root'

        if dest_folder_id:
            from apps.folders.models import Folder
            dest_folder = get_object_or_404(Folder, id=dest_folder_id, owner=request.user)
            file_record.folder = dest_folder
        else:
            file_record.folder = None

        file_record.save(update_fields=['folder', 'updated_at'])
        new_folder_name = file_record.folder.name if file_record.folder else 'Root'

        ActivityLog.log(
            user=request.user,
            action='move',
            target_type='file',
            target_id=str(file_record.id),
            target_name=file_record.name,
            details={'from': old_folder_name, 'to': new_folder_name},
        )

        return Response(FileSerializer(file_record).data)


class FileCopyView(APIView):
    """Copy a file to a folder."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        file_record = get_object_or_404(File, pk=pk, owner=request.user, is_trashed=False)

        serializer = FileCopySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dest_folder_id = serializer.validated_data.get('destination_folder')
        new_name = serializer.validated_data.get('new_name') or f"Copy of {file_record.name}"

        dest_folder = None
        if dest_folder_id:
            from apps.folders.models import Folder
            dest_folder = get_object_or_404(Folder, id=dest_folder_id, owner=request.user)

        from utils.storage_backend import storage_backend
        new_key = storage_backend.generate_object_key(
            user_id=str(request.user.id),
            filename=new_name,
        )

        storage_backend.copy_file(
            source_key=file_record.storage_key,
            destination_key=new_key,
            source_bucket=file_record.storage_bucket,
        )

        new_file = File.objects.create(
            owner=request.user,
            folder=dest_folder,
            name=new_name,
            original_name=file_record.original_name,
            size=file_record.size,
            mime_type=file_record.mime_type,
            extension=file_record.extension,
            storage_key=new_key,
            storage_bucket=file_record.storage_bucket,
            checksum=file_record.checksum,
            description=file_record.description,
            tags=file_record.tags,
        )

        request.user.storage_quota.add_usage(new_file.size)

        ActivityLog.log(
            user=request.user,
            action='copy',
            target_type='file',
            target_id=str(new_file.id),
            target_name=new_file.name,
            details={'source_file': str(file_record.id)},
        )

        return Response(FileSerializer(new_file).data, status=status.HTTP_201_CREATED)


class StarFileView(APIView):
    """Toggle star status on a file."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        file_record = get_object_or_404(File, pk=pk, owner=request.user, is_trashed=False)
        file_record.is_starred = not file_record.is_starred
        file_record.save(update_fields=['is_starred', 'updated_at'])
        return Response({
            'id': str(file_record.id),
            'is_starred': file_record.is_starred,
        })


class RecentFilesView(generics.ListAPIView):
    """List recently accessed/modified files."""
    serializer_class = FileListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return File.objects.filter(
            owner=self.request.user,
            is_trashed=False,
        ).order_by('-updated_at')[:50]
