import logging
from datetime import date, timedelta

from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count
from django.db.models.functions import TruncDate

from .models import ActivityLog
from .serializers import (
    ActivityLogSerializer,
    ActivityLogListSerializer,
    ActivitySummarySerializer,
)

logger = logging.getLogger(__name__)


class ActivityFeedView(generics.ListAPIView):
    """Get the user's activity feed."""
    serializer_class = ActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = ActivityLog.objects.filter(
            user=self.request.user
        ).select_related('user')

        action_filter = self.request.query_params.get('action')
        if action_filter:
            queryset = queryset.filter(action=action_filter)

        target_type = self.request.query_params.get('target_type')
        if target_type:
            queryset = queryset.filter(target_type=target_type)

        days = self.request.query_params.get('days')
        if days:
            try:
                days = int(days)
                from django.utils import timezone
                since = timezone.now() - timedelta(days=days)
                queryset = queryset.filter(created_at__gte=since)
            except (ValueError, TypeError):
                pass

        return queryset


class ActivityDetailView(APIView):
    """Get activity details for a specific target (file or folder)."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, target_type, target_id):
        activities = ActivityLog.objects.filter(
            user=request.user,
            target_type=target_type,
            target_id=str(target_id),
        ).order_by('-created_at')[:50]

        serializer = ActivityLogSerializer(activities, many=True)
        return Response(serializer.data)


class ActivitySummaryView(APIView):
    """Get activity summary with counts per action type."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        days = int(request.query_params.get('days', 30))

        from django.utils import timezone
        since = timezone.now() - timedelta(days=days)

        summary = ActivityLog.objects.filter(
            user=request.user,
            created_at__gte=since,
        ).values('action').annotate(
            count=Count('id')
        ).order_by('-count')

        daily_counts = ActivityLog.objects.filter(
            user=request.user,
            created_at__gte=since,
        ).annotate(
            day=TruncDate('created_at')
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')

        total_actions = sum(item['count'] for item in summary)

        storage_actions = ActivityLog.objects.filter(
            user=request.user,
            action__in=['upload', 'delete', 'trash'],
            created_at__gte=since,
        ).values('action').annotate(
            count=Count('id')
        )

        return Response({
            'period_days': days,
            'total_actions': total_actions,
            'action_breakdown': ActivitySummarySerializer(summary, many=True).data,
            'daily_activity': [
                {'date': str(item['day']), 'count': item['count']}
                for item in daily_counts
            ],
            'storage_activity': {
                item['action']: item['count'] for item in storage_actions
            },
        })


class RecentActivityView(generics.ListAPIView):
    """Get the most recent activity items (lightweight)."""
    serializer_class = ActivityLogListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        limit = min(int(self.request.query_params.get('limit', 20)), 100)
        return ActivityLog.objects.filter(
            user=self.request.user
        )[:limit]
