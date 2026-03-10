"""
File service layer handling upload, download, versioning, and preview logic.
"""

import hashlib
import logging
import mimetypes
import os
from typing import Optional, BinaryIO

from django.conf import settings
from django.utils import timezone

from utils.storage_backend import storage_backend
from utils.exceptions import (
    StorageQuotaExceeded,
    FileNotFound,
    FileTooLarge,
)

logger = logging.getLogger(__name__)


class FileUploadService:
    """Handles file upload operations including validation and storage."""

    @staticmethod
    def validate_upload(user, file_obj) -> None:
        """Validate file before upload."""
        if file_obj.size > settings.MAX_UPLOAD_SIZE:
            raise FileTooLarge(
                detail=f"File size ({file_obj.size} bytes) exceeds maximum "
                       f"allowed size ({settings.MAX_UPLOAD_SIZE} bytes)."
            )

        quota = user.storage_quota
        if not quota.has_space(file_obj.size):
            raise StorageQuotaExceeded(
                detail=f"Not enough storage space. "
                       f"Available: {quota.available_bytes} bytes, "
                       f"Required: {file_obj.size} bytes."
            )

    @staticmethod
    def compute_checksum(file_obj: BinaryIO) -> str:
        """Compute SHA-256 checksum of a file."""
        sha256 = hashlib.sha256()
        file_obj.seek(0)
        for chunk in iter(lambda: file_obj.read(8192), b''):
            sha256.update(chunk)
        file_obj.seek(0)
        return sha256.hexdigest()

    @staticmethod
    def detect_mime_type(filename: str, file_obj: BinaryIO = None) -> str:
        """Detect MIME type from filename."""
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or 'application/octet-stream'

    @staticmethod
    def get_extension(filename: str) -> str:
        """Extract file extension."""
        _, ext = os.path.splitext(filename)
        return ext.lower().lstrip('.') if ext else ''

    @classmethod
    def upload_file(cls, user, file_obj, folder=None, description='') -> 'File':
        """
        Upload a new file.

        Args:
            user: The file owner
            file_obj: Django UploadedFile object
            folder: Optional parent folder
            description: Optional file description

        Returns:
            File model instance
        """
        from apps.files.models import File, FileVersion

        cls.validate_upload(user, file_obj)

        filename = file_obj.name
        mime_type = cls.detect_mime_type(filename, file_obj)
        extension = cls.get_extension(filename)
        checksum = cls.compute_checksum(file_obj)

        object_key = storage_backend.generate_object_key(
            user_id=str(user.id),
            filename=filename,
        )

        result = storage_backend.upload_file(
            file_obj=file_obj,
            object_key=object_key,
            content_type=mime_type,
            metadata={
                'owner': str(user.id),
                'original_name': filename,
                'checksum': checksum,
            },
        )

        file_record = File.objects.create(
            owner=user,
            folder=folder,
            name=filename,
            original_name=filename,
            size=result['size'],
            mime_type=mime_type,
            extension=extension,
            storage_key=result['key'],
            storage_bucket=result['bucket'],
            checksum=checksum,
            etag=result.get('etag', ''),
            description=description,
            current_version=1,
        )

        FileVersion.objects.create(
            file=file_record,
            version_number=1,
            storage_key=result['key'],
            storage_bucket=result['bucket'],
            size=result['size'],
            checksum=checksum,
            etag=result.get('etag', ''),
            uploaded_by=user,
            comment='Initial upload',
        )

        user.storage_quota.add_usage(result['size'])

        logger.info(f"File uploaded: {filename} by {user.email} ({result['size']} bytes)")
        return file_record

    @classmethod
    def upload_new_version(cls, user, file_record, file_obj, comment='') -> 'FileVersion':
        """
        Upload a new version of an existing file.

        Args:
            user: The user uploading
            file_record: Existing File instance
            file_obj: New file data
            comment: Version comment

        Returns:
            FileVersion model instance
        """
        from apps.files.models import FileVersion

        cls.validate_upload(user, file_obj)

        filename = file_obj.name
        mime_type = cls.detect_mime_type(filename, file_obj)
        checksum = cls.compute_checksum(file_obj)

        new_version_number = file_record.current_version + 1

        version_key = storage_backend.generate_object_key(
            user_id=str(file_record.owner.id),
            filename=filename,
            prefix='versions',
        )

        result = storage_backend.upload_file(
            file_obj=file_obj,
            object_key=version_key,
            content_type=mime_type,
            bucket_name=f"{settings.MINIO_BUCKET_NAME}-versions",
            metadata={
                'file_id': str(file_record.id),
                'version': str(new_version_number),
                'uploaded_by': str(user.id),
            },
        )

        version = FileVersion.objects.create(
            file=file_record,
            version_number=new_version_number,
            storage_key=result['key'],
            storage_bucket=f"{settings.MINIO_BUCKET_NAME}-versions",
            size=result['size'],
            checksum=checksum,
            etag=result.get('etag', ''),
            uploaded_by=user,
            comment=comment or f'Version {new_version_number}',
        )

        old_size = file_record.size
        file_record.size = result['size']
        file_record.mime_type = mime_type
        file_record.checksum = checksum
        file_record.current_version = new_version_number
        file_record.storage_key = result['key']
        file_record.storage_bucket = result['bucket']
        file_record.etag = result.get('etag', '')
        file_record.save()

        size_diff = result['size'] - old_size
        if size_diff > 0:
            user.storage_quota.add_usage(size_diff)
        elif size_diff < 0:
            user.storage_quota.subtract_usage(abs(size_diff))

        logger.info(
            f"New version {new_version_number} uploaded for {file_record.name} "
            f"by {user.email}"
        )
        return version


class FileDownloadService:
    """Handles file download operations."""

    @staticmethod
    def get_download_url(file_record, expiration: int = 3600) -> str:
        """Generate a presigned download URL."""
        return storage_backend.generate_presigned_url(
            object_key=file_record.storage_key,
            bucket_name=file_record.storage_bucket,
            expiration=expiration,
        )

    @staticmethod
    def get_file_content(file_record) -> BinaryIO:
        """Download file content as BytesIO."""
        return storage_backend.download_file(
            object_key=file_record.storage_key,
            bucket_name=file_record.storage_bucket,
        )

    @staticmethod
    def get_version_download_url(version, expiration: int = 3600) -> str:
        """Generate a presigned download URL for a specific version."""
        return storage_backend.generate_presigned_url(
            object_key=version.storage_key,
            bucket_name=version.storage_bucket,
            expiration=expiration,
        )

    @staticmethod
    def record_access(file_record) -> None:
        """Update last accessed timestamp."""
        file_record.last_accessed_at = timezone.now()
        file_record.save(update_fields=['last_accessed_at'])


class FileVersionService:
    """Handles file version management."""

    @staticmethod
    def get_versions(file_record):
        """Get all versions of a file."""
        from apps.files.models import FileVersion
        return FileVersion.objects.filter(file=file_record).order_by('-version_number')

    @staticmethod
    def restore_version(file_record, version_number: int, user) -> 'File':
        """
        Restore a file to a previous version.
        This creates a new version that is a copy of the target version.
        """
        from apps.files.models import FileVersion

        try:
            target_version = FileVersion.objects.get(
                file=file_record,
                version_number=version_number,
            )
        except FileVersion.DoesNotExist:
            raise FileNotFound(detail=f"Version {version_number} not found.")

        new_version_number = file_record.current_version + 1

        new_key = storage_backend.generate_object_key(
            user_id=str(file_record.owner.id),
            filename=file_record.name,
            prefix='versions',
        )

        storage_backend.copy_file(
            source_key=target_version.storage_key,
            destination_key=new_key,
            source_bucket=target_version.storage_bucket,
            destination_bucket=f"{settings.MINIO_BUCKET_NAME}-versions",
        )

        new_version = FileVersion.objects.create(
            file=file_record,
            version_number=new_version_number,
            storage_key=new_key,
            storage_bucket=f"{settings.MINIO_BUCKET_NAME}-versions",
            size=target_version.size,
            checksum=target_version.checksum,
            uploaded_by=user,
            comment=f'Restored from version {version_number}',
        )

        old_size = file_record.size
        file_record.size = target_version.size
        file_record.checksum = target_version.checksum
        file_record.current_version = new_version_number
        file_record.storage_key = new_key
        file_record.storage_bucket = f"{settings.MINIO_BUCKET_NAME}-versions"
        file_record.save()

        size_diff = target_version.size - old_size
        if size_diff > 0:
            user.storage_quota.add_usage(size_diff)
        elif size_diff < 0:
            user.storage_quota.subtract_usage(abs(size_diff))

        logger.info(
            f"File {file_record.name} restored to version {version_number} "
            f"(now v{new_version_number}) by {user.email}"
        )
        return file_record


class FilePreviewService:
    """Handles file preview generation."""

    @staticmethod
    def get_preview_url(file_record, expiration: int = 3600) -> Optional[dict]:
        """
        Get preview information for a file.

        Returns dict with preview_type and url, or None if not previewable.
        """
        if not file_record.is_previewable:
            return None

        preview_url = storage_backend.generate_presigned_url(
            object_key=file_record.storage_key,
            bucket_name=file_record.storage_bucket,
            expiration=expiration,
        )

        return {
            'preview_type': file_record.file_type_category,
            'url': preview_url,
            'mime_type': file_record.mime_type,
            'name': file_record.name,
            'size': file_record.size,
        }

    @staticmethod
    def get_text_preview(file_record, max_bytes: int = 1048576) -> Optional[dict]:
        """
        Get text content preview for text files.
        Limited to max_bytes (default 1MB).
        """
        if file_record.file_type_category != 'text':
            return None

        try:
            content = storage_backend.download_file(
                object_key=file_record.storage_key,
                bucket_name=file_record.storage_bucket,
            )
            text = content.read(max_bytes).decode('utf-8', errors='replace')
            truncated = file_record.size > max_bytes
            return {
                'preview_type': 'text',
                'content': text,
                'truncated': truncated,
                'mime_type': file_record.mime_type,
            }
        except Exception as e:
            logger.error(f"Failed to generate text preview for {file_record.name}: {e}")
            return None


class FileDeletionService:
    """Handles file deletion (soft and hard)."""

    @staticmethod
    def soft_delete(file_record) -> None:
        """Move file to trash (soft delete)."""
        file_record.is_trashed = True
        file_record.trashed_at = timezone.now()
        file_record.save(update_fields=['is_trashed', 'trashed_at', 'updated_at'])
        logger.info(f"File soft-deleted: {file_record.name}")

    @staticmethod
    def restore(file_record) -> None:
        """Restore file from trash."""
        file_record.is_trashed = False
        file_record.trashed_at = None
        file_record.save(update_fields=['is_trashed', 'trashed_at', 'updated_at'])
        logger.info(f"File restored: {file_record.name}")

    @staticmethod
    def hard_delete(file_record) -> None:
        """Permanently delete file and all versions from storage."""
        from apps.files.models import FileVersion

        versions = FileVersion.objects.filter(file=file_record)
        version_keys = [v.storage_key for v in versions]

        storage_backend.delete_file(
            object_key=file_record.storage_key,
            bucket_name=file_record.storage_bucket,
        )

        if version_keys:
            for v in versions:
                storage_backend.delete_file(
                    object_key=v.storage_key,
                    bucket_name=v.storage_bucket,
                )

        file_record.owner.storage_quota.subtract_usage(file_record.size)

        file_name = file_record.name
        owner_email = file_record.owner.email
        file_record.delete()
        logger.info(f"File permanently deleted: {file_name} by {owner_email}")
