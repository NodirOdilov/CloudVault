"""
Celery tasks for file operations.
"""

import logging

from celery import shared_task
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_file_upload(self, file_id):
    """
    Post-upload processing: generate thumbnails, extract metadata, etc.
    """
    from apps.files.models import File

    try:
        file_record = File.objects.get(id=file_id)
        logger.info(f"Processing uploaded file: {file_record.name}")

        # Future enhancements: thumbnail generation, virus scanning, etc.
        logger.info(f"File processing complete: {file_record.name}")

    except File.DoesNotExist:
        logger.error(f"File {file_id} not found for processing")
    except Exception as exc:
        logger.error(f"Error processing file {file_id}: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def cleanup_orphaned_storage(self):
    """
    Clean up storage objects that have no corresponding database records.
    Runs periodically to handle failed uploads or incomplete deletions.
    """
    from apps.files.models import File
    from utils.storage_backend import storage_backend

    try:
        logger.info("Starting orphaned storage cleanup")

        all_keys = set()
        db_keys = set(
            File.objects.values_list('storage_key', flat=True)
        )

        try:
            paginator = storage_backend.client.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=settings.MINIO_BUCKET_NAME):
                for obj in page.get('Contents', []):
                    all_keys.add(obj['Key'])
        except Exception as e:
            logger.error(f"Failed to list storage objects: {e}")
            return

        orphaned = all_keys - db_keys

        if orphaned:
            logger.info(f"Found {len(orphaned)} orphaned objects")
            for key in orphaned:
                storage_backend.delete_file(key)
            logger.info(f"Cleaned up {len(orphaned)} orphaned objects")
        else:
            logger.info("No orphaned objects found")

    except Exception as exc:
        logger.error(f"Error during orphaned storage cleanup: {exc}")
        raise self.retry(exc=exc)


@shared_task
def recalculate_user_storage(user_id):
    """Recalculate storage usage for a specific user."""
    from apps.accounts.models import User

    try:
        user = User.objects.get(id=user_id)
        quota = user.storage_quota
        old_usage = quota.used_bytes
        new_usage = quota.recalculate_usage()
        logger.info(
            f"Storage recalculated for {user.email}: "
            f"{old_usage} -> {new_usage} bytes"
        )
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for storage recalculation")
