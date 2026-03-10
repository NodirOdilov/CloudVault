import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model for CloudVault."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    avatar = models.URLField(max_length=500, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username

    @property
    def storage_used(self):
        """Calculate total storage used by this user in bytes."""
        from apps.files.models import File
        result = File.objects.filter(
            owner=self, is_trashed=False
        ).aggregate(total=models.Sum('size'))
        return result['total'] or 0

    @property
    def storage_used_display(self):
        """Human-readable storage usage."""
        return self._format_bytes(self.storage_used)

    @property
    def storage_quota_display(self):
        """Human-readable storage quota."""
        try:
            return self._format_bytes(self.storage_quota.quota_bytes)
        except StorageQuota.DoesNotExist:
            return self._format_bytes(settings.DEFAULT_STORAGE_QUOTA)

    @staticmethod
    def _format_bytes(num_bytes):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if abs(num_bytes) < 1024.0:
                return f"{num_bytes:.1f} {unit}"
            num_bytes /= 1024.0
        return f"{num_bytes:.1f} PB"


class StorageQuota(models.Model):
    """Storage quota settings per user."""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='storage_quota',
    )
    quota_bytes = models.BigIntegerField(
        default=5368709120,  # 5 GB
        help_text='Storage quota in bytes',
    )
    used_bytes = models.BigIntegerField(
        default=0,
        help_text='Cached storage usage in bytes',
    )
    last_calculated = models.DateTimeField(
        auto_now=True,
        help_text='Last time usage was recalculated',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'storage_quotas'
        verbose_name = 'Storage Quota'
        verbose_name_plural = 'Storage Quotas'

    def __str__(self):
        return f"{self.user.email} - {self.usage_percentage:.1f}% used"

    @property
    def available_bytes(self):
        return max(0, self.quota_bytes - self.used_bytes)

    @property
    def usage_percentage(self):
        if self.quota_bytes == 0:
            return 100.0
        return (self.used_bytes / self.quota_bytes) * 100

    def recalculate_usage(self):
        """Recalculate actual storage usage from files."""
        self.used_bytes = self.user.storage_used
        self.save(update_fields=['used_bytes', 'last_calculated', 'updated_at'])
        return self.used_bytes

    def has_space(self, additional_bytes: int) -> bool:
        """Check if user has enough space for additional bytes."""
        return (self.used_bytes + additional_bytes) <= self.quota_bytes

    def add_usage(self, size_bytes: int):
        """Increment usage by given bytes."""
        self.used_bytes = models.F('used_bytes') + size_bytes
        self.save(update_fields=['used_bytes', 'updated_at'])
        self.refresh_from_db()

    def subtract_usage(self, size_bytes: int):
        """Decrement usage by given bytes."""
        from django.db.models.functions import Greatest
        StorageQuota.objects.filter(pk=self.pk).update(
            used_bytes=Greatest(models.F('used_bytes') - size_bytes, models.Value(0))
        )
        self.refresh_from_db()
