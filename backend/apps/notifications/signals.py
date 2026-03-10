"""
Signal handlers that automatically create notifications for key events.
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender='files.FileShare')
def notify_file_shared(sender, instance, created, **kwargs):
    """Send notification when a file is shared with someone."""
    if created:
        from .models import Notification
        try:
            Notification.notify_file_shared(
                owner=instance.shared_by,
                shared_with=instance.shared_with,
                file_record=instance.file,
                permission=instance.permission,
            )
            logger.info(
                f"Notification sent: file shared {instance.file.name} "
                f"with {instance.shared_with.email}"
            )
        except Exception as e:
            logger.error(f"Failed to send file share notification: {e}")


@receiver(post_save, sender='teams.TeamInvitation')
def notify_team_invitation(sender, instance, created, **kwargs):
    """Send notification when someone is invited to a team."""
    if created:
        from .models import Notification
        try:
            notification = Notification.notify_team_invitation(instance)
            if notification:
                logger.info(
                    f"Notification sent: team invitation to {instance.invited_email} "
                    f"for {instance.team.name}"
                )
        except Exception as e:
            logger.error(f"Failed to send team invitation notification: {e}")


@receiver(post_save, sender='accounts.StorageQuota')
def check_storage_warning(sender, instance, **kwargs):
    """Check if user storage is approaching quota and warn them."""
    from .models import Notification

    percentage = instance.usage_percentage

    if percentage >= 90:
        existing = Notification.objects.filter(
            recipient=instance.user,
            notification_type='storage_warning',
            is_read=False,
        ).exists()

        if not existing:
            try:
                Notification.notify_storage_warning(instance.user, percentage)
                logger.info(
                    f"Storage warning sent to {instance.user.email}: "
                    f"{percentage:.1f}% used"
                )
            except Exception as e:
                logger.error(f"Failed to send storage warning: {e}")
