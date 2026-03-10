import uuid

from django.conf import settings
from django.db import models


class Folder(models.Model):
    """Represents a folder in the file hierarchy."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='folders',
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
    )
    name = models.CharField(max_length=255)
    color = models.CharField(max_length=7, default='#6B7280', help_text='Hex color code')
    description = models.TextField(blank=True, default='')

    is_trashed = models.BooleanField(default=False, db_index=True)
    trashed_at = models.DateTimeField(null=True, blank=True)
    is_starred = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'folders'
        ordering = ['name']
        indexes = [
            models.Index(fields=['owner', 'parent', 'is_trashed']),
            models.Index(fields=['owner', 'is_trashed']),
            models.Index(fields=['name']),
        ]
        unique_together = ['owner', 'parent', 'name']
        verbose_name = 'Folder'
        verbose_name_plural = 'Folders'

    def __str__(self):
        return f"{self.name} ({self.owner.email})"

    @property
    def path(self):
        """Get full path of the folder."""
        parts = [self.name]
        current = self.parent
        while current:
            parts.insert(0, current.name)
            current = current.parent
        return '/'.join(parts)

    @property
    def breadcrumb(self):
        """Get breadcrumb trail as list of dicts."""
        trail = [{'id': str(self.id), 'name': self.name}]
        current = self.parent
        while current:
            trail.insert(0, {'id': str(current.id), 'name': current.name})
            current = current.parent
        return trail

    @property
    def depth(self):
        """Calculate nesting depth."""
        depth = 0
        current = self.parent
        while current:
            depth += 1
            current = current.parent
        return depth

    @property
    def total_size(self):
        """Calculate total size of all files in this folder and subfolders."""
        from apps.files.models import File
        total = File.objects.filter(
            folder=self, is_trashed=False
        ).aggregate(total=models.Sum('size'))['total'] or 0

        for child in self.children.filter(is_trashed=False):
            total += child.total_size
        return total

    @property
    def file_count(self):
        """Count files in this folder only."""
        return self.files.filter(is_trashed=False).count()

    @property
    def subfolder_count(self):
        """Count immediate subfolders."""
        return self.children.filter(is_trashed=False).count()

    def get_all_descendants(self):
        """Get all descendant folders recursively."""
        descendants = []
        for child in self.children.filter(is_trashed=False):
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants

    def is_ancestor_of(self, folder):
        """Check if this folder is an ancestor of another folder."""
        current = folder.parent
        while current:
            if current.id == self.id:
                return True
            current = current.parent
        return False


class FolderPermission(models.Model):
    """Permissions for shared folders."""
    PERMISSION_CHOICES = [
        ('view', 'View Only'),
        ('edit', 'Can Edit'),
        ('upload', 'Can Upload'),
        ('manage', 'Full Access'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    folder = models.ForeignKey(
        Folder,
        on_delete=models.CASCADE,
        related_name='permissions',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='folder_permissions',
    )
    permission = models.CharField(max_length=20, choices=PERMISSION_CHOICES, default='view')
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='granted_folder_permissions',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'folder_permissions'
        unique_together = ['folder', 'user']
        verbose_name = 'Folder Permission'
        verbose_name_plural = 'Folder Permissions'

    def __str__(self):
        return f"{self.user.email} -> {self.folder.name} ({self.permission})"
