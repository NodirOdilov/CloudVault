"""
Development settings for CloudVault.
"""

from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ['*']

# Use console email backend in development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable throttling in development
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []  # noqa: F405

# CORS - allow all origins in development
CORS_ALLOW_ALL_ORIGINS = True

# Simpler logging in development
LOGGING['handlers'] = {  # noqa: F405
    'console': {
        'class': 'logging.StreamHandler',
        'formatter': 'verbose',
    },
}
LOGGING['root']['handlers'] = ['console']  # noqa: F405
LOGGING['loggers']['apps']['handlers'] = ['console']  # noqa: F405
LOGGING['loggers']['django']['handlers'] = ['console']  # noqa: F405

# Create logs directory
import os
os.makedirs(BASE_DIR / 'logs', exist_ok=True)  # noqa: F405
