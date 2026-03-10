import uuid

from django.conf import settings
from django.db import models


class File(models.Model):
    """Represents a file stored in the system."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='files',
    )
    folder = models.ForeignKey(
        'folders.Folder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='files',
    )
    name = models.CharField(max_length=500)
    original_name = models.CharField(max_length=500)
    size = models.BigIntegerField(default=0, help_text='File size in bytes')
    mime_type = models.CharField(max_length=255, default='application/octet-stream')
    extension = models.CharField(max_length=50, blank=True, default='')
    storage_key = models.CharField(max_length=1000, unique=True, help_text='S3/MinIO object key')
    storage_bucket = models.CharField(max_length=255, default='cloudvault-files')
    checksum = models.CharField(max_length=64, blank=True, default='', help_text='SHA-256 checksum')
    etag = models.CharField(max_length=255, blank=True, default='')

    # Version tracking
    current_version = models.PositiveIntegerField(default=1)

    # Metadata
    description = models.TextField(blank=True, default='')
    tags = models.JSONField(default=list, blank=True)

    # Status flags
    is_trashed = models.BooleanField(default=False, db_index=True)
    trashed_at = models.DateTimeField(null=True, blank=True)
    is_starred = models.BooleanField(default=False, db_index=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_accessed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'files'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['owner', 'is_trashed']),
            models.Index(fields=['owner', 'folder', 'is_trashed']),
            models.Index(fields=['name']),
            models.Index(fields=['mime_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
        ]
        verbose_name = 'File'
        verbose_name_plural = 'Files'

    def __str__(self):
        return f"{self.name} ({self.owner.email})"

    @property
    def size_display(self):
        """Human-readable file size."""
        num = self.size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if abs(num) < 1024.0:
                return f"{num:.1f} {unit}"
            num /= 1024.0
        return f"{num:.1f} PB"

    @property
    def file_type_category(self):
        """Categorize file by MIME type."""
        if self.mime_type in settings.PREVIEWABLE_IMAGE_TYPES:
            return 'image'
        elif self.mime_type in settings.PREVIEWABLE_PDF_TYPES:
            return 'pdf'
        elif self.mime_type in settings.PREVIEWABLE_TEXT_TYPES:
            return 'text'
        elif self.mime_type in settings.PREVIEWABLE_AUDIO_TYPES:
            return 'audio'
        elif self.mime_type in settings.PREVIEWABLE_VIDEO_TYPES:
            return 'video'
        elif self.mime_type.startswith('application/vnd'):
            return 'document'
        elif self.mime_type.startswith('application/zip') or self.mime_type.endswith('compressed'):
            return 'archive'
        return 'other'

    @property
    def is_previewable(self):
        """Check if this file can be previewed in the browser."""
        previewable = (
            settings.PREVIEWABLE_IMAGE_TYPES +
            settings.PREVIEWABLE_TEXT_TYPES +
            settings.PREVIEWABLE_PDF_TYPES +
            settings.PREVIEWABLE_AUDIO_TYPES +
            settings.PREVIEWABLE_VIDEO_TYPES
        )
        return self.mime_type in previewable

    @property
    def path(self):
        """Get full path of the file including folder hierarchy."""
        parts = [self.name]
        folder = self.folder
        while folder:
            parts.insert(0, folder.name)
            folder = folder.parent
        return '/'.join(parts)


class FileVersion(models.Model):
    """Tracks file versions for version history."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.ForeignKey(
        File,
        on_delete=models.CASCADE,
        related_name='versions',
    )
    version_number = models.PositiveIntegerField()
    storage_key = models.CharField(max_length=1000, help_text='S3/MinIO object key for this version')
    storage_bucket = models.CharField(max_length=255, default='cloudvault-files-versions')
    size = models.BigIntegerField(default=0)
    checksum = models.CharField(max_length=64, blank=True, default='')
    etag = models.CharField(max_length=255, blank=True, default='')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='file_versions',
    )
    comment = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'file_versions'
        ordering = ['-version_number']
        unique_together = ['file', 'version_number']
        verbose_name = 'File Version'
        verbose_name_plural = 'File Versions'

    def __str__(self):
        return f"{self.file.name} v{self.version_number}"


class FileShare(models.Model):
    """Direct file sharing with specific users."""
    PERMISSION_CHOICES = [
        ('view', 'View Only'),
        ('edit', 'Can Edit'),
        ('download', 'Can Download'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.ForeignKey(
        File,
        on_delete=models.CASCADE,
        related_name='shares',
    )
    shared_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='files_shared_by',
    )
    shared_with = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='files_shared_with',
    )
    permission = models.CharField(max_length=20, choices=PERMISSION_CHOICES, default='view')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'file_shares'
        unique_together = ['file', 'shared_with']
        verbose_name = 'File Share'
        verbose_name_plural = 'File Shares'

    def __str__(self):
        return f"{self.file.name} shared with {self.shared_with.email} ({self.permission})"


class SharedLink(models.Model):
    """Public shareable links for files."""
    PERMISSION_CHOICES = [
        ('view', 'View Only'),
        ('download', 'Can Download'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.ForeignKey(
        File,
        on_delete=models.CASCADE,
        related_name='shared_links',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_shared_links',
    )
    token = models.CharField(max_length=64, unique=True, db_index=True)
    permission = models.CharField(max_length=20, choices=PERMISSION_CHOICES, default='view')
    password = models.CharField(max_length=128, blank=True, default='')
    expires_at = models.DateTimeField(null=True, blank=True)
    max_downloads = models.PositiveIntegerField(null=True, blank=True)
    download_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shared_links'
        ordering = ['-created_at']
        verbose_name = 'Shared Link'
        verbose_name_plural = 'Shared Links'

    def __str__(self):
        return f"Link for {self.file.name} ({self.token[:8]}...)"

    @property
    def is_expired(self):
        if self.expires_at is None:
            return False
        from django.utils import timezone
        return timezone.now() > self.expires_at

    @property
    def download_limit_reached(self):
        if self.max_downloads is None:
            return False
        return self.download_count >= self.max_downloads

    @property
    def is_accessible(self):
        return self.is_active and not self.is_expired and not self.download_limit_reached
