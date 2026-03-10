"""
MinIO (S3-compatible) storage backend for CloudVault.
Provides file upload, download, deletion, and presigned URL generation.
"""

import io
import logging
import uuid
from typing import Optional, BinaryIO

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from django.conf import settings

logger = logging.getLogger(__name__)


class MinIOStorageBackend:
    """S3-compatible storage backend using MinIO."""

    def __init__(self):
        self._client = None
        self._resource = None

    @property
    def client(self):
        if self._client is None:
            self._client = boto3.client(
                's3',
                endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME,
                use_ssl=settings.AWS_S3_USE_SSL,
                verify=settings.AWS_S3_VERIFY,
                config=Config(
                    signature_version='s3v4',
                    s3={'addressing_style': 'path'},
                    retries={'max_attempts': 3, 'mode': 'standard'},
                ),
            )
        return self._client

    def _ensure_bucket(self, bucket_name: str) -> None:
        """Create bucket if it does not exist."""
        try:
            self.client.head_bucket(Bucket=bucket_name)
        except ClientError:
            try:
                self.client.create_bucket(Bucket=bucket_name)
                logger.info(f"Created bucket: {bucket_name}")
            except ClientError as e:
                logger.error(f"Failed to create bucket {bucket_name}: {e}")
                raise

    def generate_object_key(self, user_id: int, filename: str, prefix: str = '') -> str:
        """Generate a unique object key for storage."""
        unique_id = uuid.uuid4().hex[:12]
        if prefix:
            return f"{prefix}/{user_id}/{unique_id}/{filename}"
        return f"users/{user_id}/{unique_id}/{filename}"

    def upload_file(
        self,
        file_obj: BinaryIO,
        object_key: str,
        content_type: str = 'application/octet-stream',
        bucket_name: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        """
        Upload a file to MinIO.

        Returns:
            dict with 'key', 'bucket', 'size', 'etag'
        """
        bucket = bucket_name or settings.MINIO_BUCKET_NAME
        self._ensure_bucket(bucket)

        extra_args = {'ContentType': content_type}
        if metadata:
            extra_args['Metadata'] = {k: str(v) for k, v in metadata.items()}

        file_obj.seek(0, 2)
        file_size = file_obj.tell()
        file_obj.seek(0)

        try:
            response = self.client.put_object(
                Bucket=bucket,
                Key=object_key,
                Body=file_obj,
                ContentType=content_type,
                Metadata=metadata or {},
            )
            logger.info(f"Uploaded file to {bucket}/{object_key} ({file_size} bytes)")
            return {
                'key': object_key,
                'bucket': bucket,
                'size': file_size,
                'etag': response.get('ETag', '').strip('"'),
            }
        except ClientError as e:
            logger.error(f"Failed to upload file to {bucket}/{object_key}: {e}")
            raise

    def download_file(
        self,
        object_key: str,
        bucket_name: Optional[str] = None,
    ) -> BinaryIO:
        """Download a file from MinIO and return as BytesIO."""
        bucket = bucket_name or settings.MINIO_BUCKET_NAME

        try:
            response = self.client.get_object(Bucket=bucket, Key=object_key)
            content = io.BytesIO(response['Body'].read())
            content.seek(0)
            return content
        except ClientError as e:
            logger.error(f"Failed to download file from {bucket}/{object_key}: {e}")
            raise

    def delete_file(
        self,
        object_key: str,
        bucket_name: Optional[str] = None,
    ) -> bool:
        """Delete a file from MinIO."""
        bucket = bucket_name or settings.MINIO_BUCKET_NAME

        try:
            self.client.delete_object(Bucket=bucket, Key=object_key)
            logger.info(f"Deleted file from {bucket}/{object_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete file from {bucket}/{object_key}: {e}")
            return False

    def delete_files(
        self,
        object_keys: list,
        bucket_name: Optional[str] = None,
    ) -> bool:
        """Delete multiple files from MinIO."""
        bucket = bucket_name or settings.MINIO_BUCKET_NAME

        try:
            objects = [{'Key': key} for key in object_keys]
            self.client.delete_objects(
                Bucket=bucket,
                Delete={'Objects': objects},
            )
            logger.info(f"Deleted {len(object_keys)} files from {bucket}")
            return True
        except ClientError as e:
            logger.error(f"Failed to batch delete files from {bucket}: {e}")
            return False

    def copy_file(
        self,
        source_key: str,
        destination_key: str,
        source_bucket: Optional[str] = None,
        destination_bucket: Optional[str] = None,
    ) -> dict:
        """Copy a file within or between buckets."""
        src_bucket = source_bucket or settings.MINIO_BUCKET_NAME
        dst_bucket = destination_bucket or settings.MINIO_BUCKET_NAME
        self._ensure_bucket(dst_bucket)

        try:
            response = self.client.copy_object(
                Bucket=dst_bucket,
                Key=destination_key,
                CopySource={'Bucket': src_bucket, 'Key': source_key},
            )
            logger.info(f"Copied {src_bucket}/{source_key} to {dst_bucket}/{destination_key}")
            return {
                'key': destination_key,
                'bucket': dst_bucket,
                'etag': response.get('CopyObjectResult', {}).get('ETag', '').strip('"'),
            }
        except ClientError as e:
            logger.error(f"Failed to copy file: {e}")
            raise

    def generate_presigned_url(
        self,
        object_key: str,
        bucket_name: Optional[str] = None,
        expiration: int = 3600,
        method: str = 'get_object',
    ) -> str:
        """Generate a presigned URL for downloading or uploading."""
        bucket = bucket_name or settings.MINIO_BUCKET_NAME

        try:
            url = self.client.generate_presigned_url(
                method,
                Params={'Bucket': bucket, 'Key': object_key},
                ExpiresIn=expiration,
            )
            if hasattr(settings, 'MINIO_EXTERNAL_URL') and settings.MINIO_EXTERNAL_URL:
                url = url.replace(settings.AWS_S3_ENDPOINT_URL, settings.MINIO_EXTERNAL_URL)
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL for {bucket}/{object_key}: {e}")
            raise

    def get_file_info(
        self,
        object_key: str,
        bucket_name: Optional[str] = None,
    ) -> Optional[dict]:
        """Get metadata about a stored file."""
        bucket = bucket_name or settings.MINIO_BUCKET_NAME

        try:
            response = self.client.head_object(Bucket=bucket, Key=object_key)
            return {
                'key': object_key,
                'size': response['ContentLength'],
                'content_type': response['ContentType'],
                'last_modified': response['LastModified'],
                'etag': response['ETag'].strip('"'),
                'metadata': response.get('Metadata', {}),
            }
        except ClientError:
            return None

    def file_exists(
        self,
        object_key: str,
        bucket_name: Optional[str] = None,
    ) -> bool:
        """Check if a file exists in storage."""
        return self.get_file_info(object_key, bucket_name) is not None


# Singleton instance
storage_backend = MinIOStorageBackend()
