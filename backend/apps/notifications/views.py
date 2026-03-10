import logging

from django.utils import timezone
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification, NotificationPreference
from .serializers import (
    NotificationSerializer,
    NotificationListSerializer,
    MarkNotificationsReadSerializer,
    NotificationPreferenceSerializer,
)

logger = logging.getLogger(__name__)


class NotificationListView(generics.ListAPIView):
    """List notifications for the current user."""
    serializer_class = NotificationListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Notification.objects.filter(
            recipient=self.request.user,
            is_archived=False,
        )

        unread_only = self.request.query_params.get('unread')
        if unread_only == 'true':
            queryset = queryset.filter(is_read=False)

        notif_type = self.request.query_params.get('type')
        if notif_type:
            queryset = queryset.filter(notification_type=notif_type)

        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)

        return queryset


class NotificationDetailView(generics.RetrieveAPIView):
    """Get full details of a notification."""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.mark_read()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class MarkReadView(APIView):
    """Mark notifications as read."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = MarkNotificationsReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data.get('mark_all'):
            updated = Notification.objects.filter(
                recipient=request.user,
                is_read=False,
            ).update(is_read=True, read_at=timezone.now())
        else:
            notification_ids = serializer.validated_data.get('notification_ids', [])
            if not notification_ids:
                return Response(
                    {'error': 'Provide notification_ids or set mark_all=true.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            updated = Notification.objects.filter(
                recipient=request.user,
                id__in=notification_ids,
                is_read=False,
            ).update(is_read=True, read_at=timezone.now())

        return Response({
            'message': f'{updated} notification(s) marked as read.',
            'updated_count': updated,
        })


class ArchiveNotificationView(APIView):
    """Archive a notification."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            notification = Notification.objects.get(
                pk=pk, recipient=request.user
            )
        except Notification.DoesNotExist:
            return Response(
                {'error': 'Notification not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        notification.archive()
        return Response({'message': 'Notification archived.'})


class ClearAllNotificationsView(APIView):
    """Archive all notifications."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        updated = Notification.objects.filter(
            recipient=request.user,
            is_archived=False,
        ).update(is_archived=True)

        return Response({
            'message': f'{updated} notification(s) archived.',
            'archived_count': updated,
        })


class UnreadCountView(APIView):
    """Get count of unread notifications."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        count = Notification.get_unread_count(request.user)
        high_priority = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
            is_archived=False,
            priority__in=['high', 'urgent'],
        ).count()

        return Response({
            'unread_count': count,
            'high_priority_count': high_priority,
        })


class NotificationPreferenceView(APIView):
    """Get or update notification preferences."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        prefs, _ = NotificationPreference.objects.get_or_create(
            user=request.user
        )
        serializer = NotificationPreferenceSerializer(prefs)
        return Response(serializer.data)

    def patch(self, request):
        prefs, _ = NotificationPreference.objects.get_or_create(
            user=request.user
        )
        serializer = NotificationPreferenceSerializer(
            prefs, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
