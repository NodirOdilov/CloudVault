from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User, StorageQuota


@receiver(post_save, sender=User)
def create_storage_quota(sender, instance, created, **kwargs):
    """Automatically create a StorageQuota when a new User is created."""
    if created:
        StorageQuota.objects.get_or_create(
            user=instance,
            defaults={'quota_bytes': settings.DEFAULT_STORAGE_QUOTA},
        )
