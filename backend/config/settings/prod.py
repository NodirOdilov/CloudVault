"""
Production settings for CloudVault.
"""

from .base import *  # noqa: F401, F403

DEBUG = False

# Security settings
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Production email backend
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')  # noqa: F405
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)  # noqa: F405
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')  # noqa: F405
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')  # noqa: F405
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@cloudvault.com')  # noqa: F405

# Production logging
LOGGING['handlers']['file'] = {  # noqa: F405
    'class': 'logging.handlers.RotatingFileHandler',
    'filename': BASE_DIR / 'logs' / 'cloudvault.log',  # noqa: F405
    'maxBytes': 10 * 1024 * 1024,  # 10 MB
    'backupCount': 10,
    'formatter': 'verbose',
}
LOGGING['root']['handlers'] = ['console', 'file']  # noqa: F405
LOGGING['loggers']['apps']['handlers'] = ['console', 'file']  # noqa: F405
LOGGING['loggers']['django']['handlers'] = ['console', 'file']  # noqa: F405

# Ensure logs directory exists
import os
os.makedirs(BASE_DIR / 'logs', exist_ok=True)  # noqa: F405
