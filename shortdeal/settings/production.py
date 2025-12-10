"""
Django production settings for ShortDeal project.
"""
import os
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Add WhiteNoise middleware for production static file serving
MIDDLEWARE.insert(
    MIDDLEWARE.index('django.middleware.security.SecurityMiddleware') + 1,
    'whitenoise.middleware.WhiteNoiseMiddleware'
)

# ALLOWED_HOSTS configuration
ALLOWED_HOSTS = [
    '.railway.app',
    '127.0.0.1',
    'localhost',
]

# Add extra hosts from environment variable (comma-separated)
extra_hosts = os.getenv('ALLOWED_HOSTS_EXTRA', '')
if extra_hosts:
    ALLOWED_HOSTS.extend([host.strip() for host in extra_hosts.split(',') if host.strip()])

# Database
# Railway Postgres configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'railway'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Security settings for production
# Railway handles HTTPS, so disable Django's SSL redirect
SECURE_SSL_REDIRECT = False
# Trust Railway's proxy headers
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HSTS settings (uncomment after testing HTTPS)
# SECURE_HSTS_SECONDS = 31536000
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True

# Static files with WhiteNoise
# Use CompressedStaticFilesStorage instead of CompressedManifestStaticFilesStorage
# to avoid errors with missing source map files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# Media files configuration for production
# Railway Volume should be mounted at /app/media
# If MEDIA_ROOT env var is not set, use /app/media for Railway
import sys
if 'railway' in os.getenv('RAILWAY_ENVIRONMENT', '').lower() or os.path.exists('/app'):
    # Running on Railway
    MEDIA_ROOT = os.getenv('MEDIA_ROOT', '/app/media')
else:
    # Running locally or other environment
    MEDIA_ROOT = os.getenv('MEDIA_ROOT', BASE_DIR / 'media')
MEDIA_URL = '/media/'

# File upload settings for large video files (teaser videos up to 200MB)
DATA_UPLOAD_MAX_MEMORY_SIZE = 250 * 1024 * 1024  # 250MB max total request size
FILE_UPLOAD_MAX_MEMORY_SIZE = 250 * 1024 * 1024  # 250MB per file in memory

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
    },
}

# Email configuration
EMAIL_BACKEND = os.getenv(
    'EMAIL_BACKEND',
    'django.core.mail.backends.smtp.EmailBackend'
)
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@shortdeal.com')

# Log email configuration (without password) for debugging
import logging
logger = logging.getLogger(__name__)
logger.info(
    f"Email configuration: "
    f"BACKEND={EMAIL_BACKEND}, "
    f"HOST={EMAIL_HOST}, "
    f"PORT={EMAIL_PORT}, "
    f"TLS={EMAIL_USE_TLS}, "
    f"USER={'[SET]' if EMAIL_HOST_USER else '[NOT SET]'}, "
    f"PASSWORD={'[SET]' if EMAIL_HOST_PASSWORD else '[NOT SET]'}"
)

# CORS settings for production
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '').split(',')
if not CORS_ALLOWED_ORIGINS or CORS_ALLOWED_ORIGINS == ['']:
    CORS_ALLOWED_ORIGINS = []
