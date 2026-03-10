"""
Custom exception handling for CloudVault API.
"""

import logging

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler providing consistent error response format.
    """
    if isinstance(exc, DjangoValidationError):
        exc = APIException(detail=exc.messages)
        exc.status_code = status.HTTP_400_BAD_REQUEST

    response = exception_handler(exc, context)

    if response is not None:
        error_payload = {
            'error': True,
            'status_code': response.status_code,
        }

        if isinstance(response.data, dict):
            error_payload['message'] = _extract_message(response.data)
            error_payload['details'] = response.data
        elif isinstance(response.data, list):
            error_payload['message'] = response.data[0] if response.data else 'An error occurred'
            error_payload['details'] = response.data
        else:
            error_payload['message'] = str(response.data)
            error_payload['details'] = None

        response.data = error_payload
    else:
        logger.exception(f"Unhandled exception in {context.get('view', 'unknown')}: {exc}")
        response = Response(
            {
                'error': True,
                'status_code': 500,
                'message': 'An unexpected error occurred. Please try again later.',
                'details': None,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response


def _extract_message(data: dict) -> str:
    """Extract a human-readable message from error details."""
    if 'detail' in data:
        return str(data['detail'])
    if 'non_field_errors' in data:
        errors = data['non_field_errors']
        return str(errors[0]) if isinstance(errors, list) else str(errors)
    for key, value in data.items():
        if isinstance(value, list) and value:
            return f"{key}: {value[0]}"
        elif isinstance(value, str):
            return f"{key}: {value}"
    return 'Validation error'


class StorageQuotaExceeded(APIException):
    """Raised when a user exceeds their storage quota."""
    status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    default_detail = 'Storage quota exceeded. Please free up space or upgrade your plan.'
    default_code = 'storage_quota_exceeded'


class FileNotFound(APIException):
    """Raised when the requested file does not exist."""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'The requested file was not found.'
    default_code = 'file_not_found'


class FileTooLarge(APIException):
    """Raised when a file exceeds the maximum upload size."""
    status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    default_detail = 'The file exceeds the maximum allowed upload size.'
    default_code = 'file_too_large'


class InvalidFileType(APIException):
    """Raised when a file type is not allowed."""
    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    default_detail = 'This file type is not supported.'
    default_code = 'invalid_file_type'


class SharePermissionDenied(APIException):
    """Raised when user lacks permission for a shared resource."""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'You do not have permission to access this shared resource.'
    default_code = 'share_permission_denied'


class SharedLinkExpired(APIException):
    """Raised when a shared link has expired."""
    status_code = status.HTTP_410_GONE
    default_detail = 'This shared link has expired.'
    default_code = 'shared_link_expired'


class VersionNotFound(APIException):
    """Raised when a file version does not exist."""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'The requested file version was not found.'
    default_code = 'version_not_found'


class FolderNotEmpty(APIException):
    """Raised when trying to permanently delete a non-empty folder."""
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'The folder is not empty. Please delete or move contents first.'
    default_code = 'folder_not_empty'
