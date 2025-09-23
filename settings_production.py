# ZAIN HMS Production Settings
# Comprehensive production configuration with performance optimization and healthcare-grade security
# This file replaces both settings_production.py and settings_security.py

import os
import django
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent

# Import base settings manually to avoid import issues
import sys
sys.path.insert(0, str(BASE_DIR))

# Base Django settings
SECRET_KEY = 'temporary-key-for-import'  # Will be overridden below
DEBUG = True  # Will be overridden below
ALLOWED_HOSTS = []  # Will be overridden below
ROOT_URLCONF = 'urls'
WSGI_APPLICATION = 'wsgi.application'

# Import base settings if available
try:
    from settings import *
except ImportError:
    pass  # Use minimal settings if base not available

import logging

# ==============================================================================
# PRODUCTION ENVIRONMENT VALIDATION
# ==============================================================================

# Ensure we're in production mode (with flexibility for testing)
environment = os.getenv('ENVIRONMENT', '')
if environment not in ['production', 'testing'] and not os.getenv('DJANGO_ALLOW_ASYNC_UNSAFE'):
    import warnings
    warnings.warn(
        "This settings file is intended for PRODUCTION use. "
        "Set ENVIRONMENT=production in your .env file for production, "
        "or ENVIRONMENT=testing for safe testing.",
        UserWarning
    )

# ==============================================================================
# CORE SECURITY SETTINGS
# ==============================================================================

# Security Keys and Debug
DEBUG = False
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY or SECRET_KEY == 'your-secret-key-here' or 'django-insecure' in SECRET_KEY:
    if os.getenv('ENVIRONMENT') == 'production':
        raise ValueError("You must set a secure SECRET_KEY in production!")
    else:
        import warnings
        warnings.warn("Using insecure SECRET_KEY for testing purposes", UserWarning)

# Production domains
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')
if not ALLOWED_HOSTS or ALLOWED_HOSTS == ['']:
    if os.getenv('ENVIRONMENT') == 'production':
        raise ValueError("You must configure ALLOWED_HOSTS for production!")
    else:
        ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']

# Custom admin URL for security
ADMIN_URL = os.getenv('ADMIN_URL', 'admin/')

# ==============================================================================
# OPTIMIZED DATABASE CONFIGURATION
# ==============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'zain_hms_production'),
        'USER': os.getenv('DB_USER', 'zain_hms_user'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': os.getenv('DB_SSL_MODE', 'require'),
            'connect_timeout': 10,
            'options': '-c default_transaction_isolation=serializable'
        },
        'CONN_MAX_AGE': 60,  # Connection pooling for performance
        'CONN_HEALTH_CHECKS': True,
        'TEST': {
            'NAME': 'test_zain_hms_production',
        },
    }
}

# Validate database password
db_password = DATABASES['default']['PASSWORD']
if not db_password:
    if os.getenv('ENVIRONMENT') == 'production':
        raise ValueError("You must set a secure database password (DB_PASSWORD)!")
    else:
        import warnings
        warnings.warn("Using database without password for testing", UserWarning)

# ==============================================================================
# HIGH-PERFORMANCE REDIS CACHING
# ==============================================================================

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
            'PASSWORD': os.getenv('REDIS_PASSWORD'),
        },
        'KEY_PREFIX': 'zain_hms_prod',
        'TIMEOUT': 300,  # 5 minutes default
    },
    'sessions': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_SESSION_URL', 'redis://127.0.0.1:6379/2'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PASSWORD': os.getenv('REDIS_PASSWORD'),
        },
        'KEY_PREFIX': 'zain_hms_sessions',
        'TIMEOUT': 3600,  # 1 hour for sessions
    },
    'templates': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_CACHE_URL', 'redis://127.0.0.1:6379/3'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PASSWORD': os.getenv('REDIS_PASSWORD'),
        },
        'KEY_PREFIX': 'zain_hms_templates',
        'TIMEOUT': 1800,  # 30 minutes for templates
    }
}

# Use Redis for sessions (performance + security)
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'sessions'

# ==============================================================================
# HTTPS AND SSL SECURITY
# ==============================================================================

# Force HTTPS in production
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# HSTS (HTTP Strict Transport Security) - Healthcare grade
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Content Security
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# ==============================================================================
# HEALTHCARE-GRADE SESSION & COOKIE SECURITY
# ==============================================================================

# Session Cookies (HIPAA Compliant)
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
SESSION_COOKIE_AGE = 3600  # 1 hour for healthcare security
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True
SESSION_TIMEOUT = 3600  # Custom timeout for middleware

# CSRF Protection
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'
CSRF_TRUSTED_ORIGINS = [
    f'https://{host}' for host in ALLOWED_HOSTS if host != '*'
]

# ==============================================================================
# HEALTHCARE PASSWORD SECURITY (HIPAA Compliant)
# ==============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        'OPTIONS': {'max_similarity': 0.7}
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 12}  # Healthcare standard
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    {
        'NAME': 'apps.core.security_validators.HealthcarePasswordValidator',
    },
]

# Authentication Settings
LOGIN_ATTEMPTS_LIMIT = 5
LOGIN_LOCKOUT_DURATION = 900  # 15 minutes
PASSWORD_RESET_TIMEOUT = 3600  # 1 hour
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# ==============================================================================
# SECURITY MIDDLEWARE STACK
# ==============================================================================

# Security middleware (order is important!)
SECURITY_MIDDLEWARE = [
    'apps.core.middleware.SecurityAuditMiddleware',
    'apps.core.middleware.IPWhitelistMiddleware',
    'apps.core.middleware.BruteForceProtectionMiddleware',
]

# Add security middleware to the beginning
MIDDLEWARE = SECURITY_MIDDLEWARE + MIDDLEWARE

# Add healthcare compliance middleware
MIDDLEWARE.extend([
    'apps.core.middleware.HealthcareComplianceMiddleware',
    'apps.core.middleware.DataEncryptionMiddleware',
    'apps.core.middleware.SessionTimeoutMiddleware',
])

# ==============================================================================
# PRODUCTION EMAIL CONFIGURATION
# ==============================================================================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@zainhms.com')
SERVER_EMAIL = os.getenv('SERVER_EMAIL', 'admin@zainhms.com')

# Admin notifications
ADMINS = [
    ('Admin', os.getenv('ADMIN_EMAIL', 'admin@zainhms.com')),
]
MANAGERS = ADMINS

# ==============================================================================
# STATIC & MEDIA FILES (CDN READY)
# ==============================================================================

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# File upload security
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

# ==============================================================================
# COMPREHENSIVE LOGGING (HIPAA AUDIT READY)
# ==============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'security': {
            'format': '[{asctime}] {levelname} {name} {message}',
            'style': '{',
        },
        'audit': {
            'format': '[{asctime}] AUDIT {message} USER:{user} IP:{ip} ACTION:{action}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/zain_hms/application.log',
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/zain_hms/security.log',
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 10,
            'formatter': 'security',
        },
        'audit_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/zain_hms/audit.log',
            'maxBytes': 50 * 1024 * 1024,  # 50MB
            'backupCount': 20,
            'formatter': 'audit',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['security_file', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'zain_hms.audit': {
            'handlers': ['audit_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['security_file'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

# ==============================================================================
# BACKUP SECURITY
# ==============================================================================

# Database backup settings
DBBACKUP_STORAGE = 'dbbackup.storage.filesystem_storage'
DBBACKUP_STORAGE_OPTIONS = {
    'location': '/var/backups/zain_hms/encrypted/',
}
DBBACKUP_ENCRYPT = True
DBBACKUP_GPG_RECIPIENT = os.getenv('BACKUP_GPG_RECIPIENT', 'backup@zainhms.com')

# ==============================================================================
# HIPAA COMPLIANCE SETTINGS
# ==============================================================================

HIPAA_COMPLIANCE = {
    'AUDIT_ALL_ACCESS': True,
    'LOG_PHI_ACCESS': True,
    'REQUIRE_STRONG_PASSWORDS': True,
    'SESSION_TIMEOUT': 3600,  # 1 hour
    'FAILED_LOGIN_ATTEMPTS': 5,
    'PASSWORD_EXPIRY_DAYS': 90,
    'DATA_RETENTION_DAYS': 2555,  # 7 years for medical records
}

# PHI (Protected Health Information) Settings
PHI_ENCRYPTION = {
    'ENCRYPT_PII_FIELDS': True,
    'ENCRYPTION_ALGORITHM': 'AES-256',
    'KEY_ROTATION_DAYS': 30,
}

# Data encryption key (use environment variable!)
DATA_ENCRYPTION_KEY = os.getenv('DATA_ENCRYPTION_KEY')

# ==============================================================================
# PERFORMANCE OPTIMIZATION
# ==============================================================================

# Template caching
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]),
]

# Cache configuration for performance
CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 300
CACHE_MIDDLEWARE_KEY_PREFIX = 'zain_hms'

# ==============================================================================
# SECURITY HEADERS
# ==============================================================================

SECURITY_HEADERS = {
    'X-Frame-Options': 'DENY',
    'X-Content-Type-Options': 'nosniff',
    'X-XSS-Protection': '1; mode=block',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
    'Content-Security-Policy': (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' cdnjs.cloudflare.com cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' cdnjs.cloudflare.com cdn.jsdelivr.net; "
        "img-src 'self' data:; "
        "font-src 'self' cdnjs.cloudflare.com cdn.jsdelivr.net; "
        "connect-src 'self'; "
        "frame-ancestors 'none';"
    ),
}

# ==============================================================================
# MONITORING & ALERTING
# ==============================================================================

# External monitoring (Sentry)
SENTRY_DSN = os.getenv('SENTRY_DSN')
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(
                transaction_style='url',
                middleware_spans=True,
                signals_spans=True,
            ),
            LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR
            ),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,  # HIPAA Compliance
        environment='production',
    )

# ==============================================================================
# RATE LIMITING
# ==============================================================================

RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'
RATELIMIT_VIEW = 'apps.core.views.ratelimited'

# ==============================================================================
# SUCCESS MESSAGE
# ==============================================================================

print("🔒 ZAIN HMS Production Settings Loaded")
print("⚕️ Healthcare-grade security enabled")
print("🚀 Performance optimization active")
print("📊 HIPAA compliance configured")