import logging

from django.db.models import Q, Value, CharField
from django.db.models.functions import Concat
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.files.models import File
from apps.files.serializers import FileListSerializer
from apps.folders.models import Folder
from apps.folders.serializers import FolderListSerializer

logger = logging.getLogger(__name__)


class GlobalSearchView(APIView):
    """Search across files and folders."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query or len(query) < 2:
            return Response(
                {'error': 'Search query must be at least 2 characters.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        search_type = request.query_params.get('type', 'all')
        limit = min(int(request.query_params.get('limit', 20)), 100)

        results = {'query': query, 'files': [], 'folders': []}

        if search_type in ('all', 'files'):
            files = self._search_files(request.user, query, limit)
            results['files'] = FileListSerializer(files, many=True).data

        if search_type in ('all', 'folders'):
            folders = self._search_folders(request.user, query, limit)
            results['folders'] = FolderListSerializer(folders, many=True).data

        results['total_count'] = len(results['files']) + len(results['folders'])

        return Response(results)

    def _search_files(self, user, query, limit):
        """Search files by name, description, and tags."""
        return File.objects.filter(
            Q(owner=user) & Q(is_trashed=False) & (
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(tags__icontains=query) |
                Q(extension__iexact=query.lstrip('.'))
            )
        ).select_related('folder').order_by('-updated_at')[:limit]

    def _search_folders(self, user, query, limit):
        """Search folders by name and description."""
        return Folder.objects.filter(
            Q(owner=user) & Q(is_trashed=False) & (
                Q(name__icontains=query) |
                Q(description__icontains=query)
            )
        ).order_by('name')[:limit]


class AdvancedSearchView(APIView):
    """Advanced search with filters for file type, size, date, etc."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        query = request.data.get('query', '').strip()
        file_types = request.data.get('file_types', [])
        min_size = request.data.get('min_size')
        max_size = request.data.get('max_size')
        date_from = request.data.get('date_from')
        date_to = request.data.get('date_to')
        folder_id = request.data.get('folder_id')
        starred_only = request.data.get('starred_only', False)
        sort_by = request.data.get('sort_by', '-updated_at')

        queryset = File.objects.filter(
            owner=request.user,
            is_trashed=False,
        )

        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(tags__icontains=query)
            )

        if file_types:
            type_filters = Q()
            type_mapping = {
                'image': Q(mime_type__startswith='image/'),
                'video': Q(mime_type__startswith='video/'),
                'audio': Q(mime_type__startswith='audio/'),
                'document': Q(mime_type__in=[
                    'application/pdf',
                    'application/msword',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'application/vnd.ms-excel',
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                ]),
                'archive': Q(mime_type__in=[
                    'application/zip',
                    'application/x-rar-compressed',
                    'application/gzip',
                    'application/x-tar',
                ]),
                'text': Q(mime_type__startswith='text/'),
            }
            for ft in file_types:
                if ft in type_mapping:
                    type_filters |= type_mapping[ft]
            queryset = queryset.filter(type_filters)

        if min_size is not None:
            queryset = queryset.filter(size__gte=int(min_size))
        if max_size is not None:
            queryset = queryset.filter(size__lte=int(max_size))

        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

        if folder_id:
            queryset = queryset.filter(folder_id=folder_id)

        if starred_only:
            queryset = queryset.filter(is_starred=True)

        allowed_sorts = [
            'name', '-name', 'size', '-size',
            'created_at', '-created_at', 'updated_at', '-updated_at',
        ]
        if sort_by in allowed_sorts:
            queryset = queryset.order_by(sort_by)

        files = queryset.select_related('folder')[:100]

        return Response({
            'count': len(files),
            'results': FileListSerializer(files, many=True).data,
        })


class SearchSuggestionsView(APIView):
    """Get search suggestions based on partial query."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response({'suggestions': []})

        file_names = list(
            File.objects.filter(
                owner=request.user,
                is_trashed=False,
                name__icontains=query,
            ).values_list('name', flat=True).distinct()[:5]
        )

        folder_names = list(
            Folder.objects.filter(
                owner=request.user,
                is_trashed=False,
                name__icontains=query,
            ).values_list('name', flat=True).distinct()[:5]
        )

        extensions = list(
            File.objects.filter(
                owner=request.user,
                is_trashed=False,
                extension__icontains=query.lstrip('.'),
            ).values_list('extension', flat=True).distinct()[:5]
        )

        suggestions = []
        for name in file_names:
            suggestions.append({'text': name, 'type': 'file'})
        for name in folder_names:
            suggestions.append({'text': name, 'type': 'folder'})
        for ext in extensions:
            if ext:
                suggestions.append({'text': f'.{ext}', 'type': 'extension'})

        return Response({'suggestions': suggestions[:10]})
