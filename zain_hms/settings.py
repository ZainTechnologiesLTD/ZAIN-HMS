# zain_hmsome one trysettings.py
import os
from pathlib import Path
from datetime import timedelta
import environ

# Initialize environment variables
env = environ.Env(
    DEBUG=(bool, False)
)
# Allow escaping of the proxy prefix (\$) so literal values that start with
# "$" (for example the currency symbol) can be represented as "\$" and
# later unescaped. This prevents django-environ from treating a literal
# "$" default as a proxy to another environment variable and recursing.
env.escape_proxy = True

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default='django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG', default=True)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1', '0.0.0.0', 'testserver'])

# Main domain for production (used by subdomain middleware)
MAIN_DOMAIN = env('MAIN_DOMAIN', default='localhost')

# Core Configuration

# Application definition
INSTALLED_APPS = [
    # Django core apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    
    # Third-party apps
    'crispy_forms',
    'crispy_bootstrap5',
    'widget_tweaks',
    'django_filters',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'django_celery_beat',
    'django_celery_results',
    'django_extensions',
    'health_check',
    'health_check.db',
    'health_check.cache',
    'health_check.storage',
    'dbbackup',
    'django_otp',
    'django_otp.plugins.otp_totp',
    'django_otp.plugins.otp_static',
    'drf_spectacular',
    'rosetta',  # Translation management
    
    # Shared/Core apps
    'apps.accounts',
    'apps.core',
    'apps.dashboard',
    'apps.reports',  # Shared reports
    'apps.analytics',
    
    # Core Healthcare Apps
    'apps.patients',
    'apps.appointments', 
    'apps.doctors',
    'apps.nurses',
    'apps.staff',
    'apps.billing',
    'apps.pharmacy',  # Keep original for now
    'apps.laboratory',
    'apps.radiology',  # Keep original for now
    'apps.emergency',
    'apps.emr',
    'apps.inventory',
    'apps.hr',
    'apps.surgery',
    'apps.telemedicine',
    'apps.room_management',
    'apps.ipd',
    'apps.opd',
    'apps.notifications',
    'apps.communications',
    'apps.contact',
    'apps.feedback',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',  # Must come after Auth middleware
    'apps.core.middleware.SecurityHeadersMiddleware',  # Enhanced security headers
    'apps.core.middleware.security.EnterpriseSecurityMiddleware',  # Enterprise security
    'apps.core.middleware.security.LoginAttemptMiddleware',  # Login attempt tracking
    # 'apps.core.timezone_middleware.HospitalTimezoneMiddleware',  # Timezone handling - disabled
    'django_otp.middleware.OTPMiddleware',  # 2FA support
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.core.middleware.ActivityLogMiddleware',  # Audit logging
    'apps.core.middleware.RateLimitMiddleware',  # API protection
    'apps.core.middleware.LoginAttemptMiddleware',  # Brute force protection
    'apps.core.middleware.SessionTimeoutMiddleware',  # Session security
    # Optional: Uncomment to enforce 2FA for staff/superusers
    # 'apps.core.middleware.EnforceTwoFactorMiddleware',  # 2FA enforcement
]

ROOT_URLCONF = 'zain_hms.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.zain_context',
                'apps.core.context_processors.notifications_context',
                'apps.core.context_processors.dashboard_stats_context',
                'apps.core.context_processors.user_permissions_context',
                'apps.core.context_processors.navigation_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'zain_hms.wsgi.application'
ASGI_APPLICATION = 'zain_hms.asgi.application'

# Database
# Using SQLite for development - easy setup and no external dependencies
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 20,
        }
    }
}

# ZAIN HMS - Unified Database Configuration (Single Database Only)
# No multi-tenant database loading - using single unified database

# Uncomment below for PostgreSQL in production
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': env('DB_NAME', default='zain_hms'),
#         'USER': env('DB_USER', default='postgres'),  
#         'PASSWORD': env('DB_PASSWORD', default='password'),
#         'HOST': env('DB_HOST', default='localhost'),
#         'PORT': env('DB_PORT', default='5432'),
#         'OPTIONS': {
#             'charset': 'utf8',
#         }
#     }
# }

# Cache - Use dummy cache for development
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Unified Database (No Multi-database routing)
DATABASE_ROUTERS = []

# Celery Configuration
CELERY_BROKER_URL = env('REDIS_URL', default='redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = 'django-db'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Custom User Model
AUTH_USER_MODEL = 'accounts.CustomUser'

# Authentication Backends - Unified ZAIN HMS authentication
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',  # Standard Django authentication for unified ZAIN HMS
]

# Password validation (centralized)
from .password_validators import AUTH_PASSWORD_VALIDATORS  # noqa: E402

# Internationalization
LANGUAGE_CODE = 'en'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Supported Languages
LANGUAGES = [
    ('en', 'English'),
    ('es', 'Español'),
    ('fr', 'Français'),
    ('ar', 'العربية'),
    # ('zh', '中文'),  # Temporarily disabled until translation files are created
    ('hi', 'हिन्दी'),
    ('pt', 'Português'),
    ('de', 'Deutsch'),
    ('it', 'Italiano'),
    # ('ja', '日本語'),  # Temporarily disabled until translation files are created
]

# Translation paths
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Login security / adaptive protections
LOGIN_ATTEMPT_LIMIT = 5              # Lockout after this many failed attempts (per IP window)
LOGIN_ATTEMPT_TIMEOUT = 300          # Lockout duration in seconds
LOGIN_CAPTCHA_THRESHOLD = 3          # Show captcha after this many failed attempts (soft challenge)

# Two-factor enforcement exclusions (paths that won't redirect when 2FA missing)
TWOFA_EXCLUDED_PATH_PREFIXES = [
    '/core/2fa', '/accounts/logout', '/accounts/login', '/admin', '/static', '/media'
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@zainhms.com')

# Login URLs
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Session Configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_SERIALIZER = 'apps.core.serializers.DateTimeAwareJSONSerializer'  # Handle datetime objects
SESSION_COOKIE_AGE = env.int('SESSION_COOKIE_AGE', default=86400)  # 24 hours default, overridden in production
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Messages Configuration
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'login': '5/min',
    },
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# API Documentation
SPECTACULAR_SETTINGS = {
    'TITLE': 'ZAIN Hospital Management System API',
    'DESCRIPTION': 'Comprehensive Hospital Management System API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
])

# Security Settings
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Enterprise Security Settings
SESSION_TIMEOUT = 3600  # 1 hour session timeout
MAX_FAILED_ATTEMPTS = 5  # Max failed login attempts before blocking
MAX_LOGIN_ATTEMPTS = 3  # Max login attempts from same IP
LOGIN_ATTEMPT_TIMEOUT = 300  # 5 minutes timeout for failed attempts

# Enhanced Session Security
SESSION_COOKIE_HTTPONLY = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True

# Enhanced CSRF Protection
CSRF_COOKIE_HTTPONLY = True
CSRF_USE_SESSIONS = True

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 1024 * 1024 * 15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 20,
            'formatter': 'verbose',
        },
        'auth_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'authentication.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 20,
            'formatter': 'verbose',
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
        # Security and authentication loggers
        'apps.accounts.backends': {
            'handlers': ['console', 'auth_file', 'security_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.accounts.middleware': {
            'handlers': ['console', 'security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'apps.accounts.security_monitor': {
            'handlers': ['console', 'security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'zain_hms.security': {
            'handlers': ['security_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# ===========================
# ZAIN HMS - UNIFIED HOSPITAL MANAGEMENT SYSTEM
# ===========================
SYSTEM_NAME = env('SYSTEM_NAME', default='ZAIN Hospital Management System')
SYSTEM_SHORT_NAME = env('SYSTEM_SHORT_NAME', default='ZAIN HMS') 
SYSTEM_DESCRIPTION = env('SYSTEM_DESCRIPTION', default='Comprehensive Healthcare Management Solution')
HOSPITAL_NAME = env('HOSPITAL_NAME', default='ZAIN Hospital Management System')
HOSPITAL_CODE = env('HOSPITAL_CODE', default='ZAIN')
CURRENCY_SYMBOL = '$'
APPOINTMENT_DURATION_MINUTES = 30
MAX_APPOINTMENTS_PER_DAY = 50
ENABLE_SMS_NOTIFICATIONS = env('ENABLE_SMS_NOTIFICATIONS', default=False)
SYSTEM_VERSION = '2.0.0'
SYSTEM_VENDOR = 'ZAIN Technologies'

# ===========================
# DJANGO ADMIN INTERFACE SETTINGS  
# ===========================
X_FRAME_OPTIONS = 'SAMEORIGIN'
SILENCED_SYSTEM_CHECKS = ['security.W019']
if DEBUG:
    # Silence production security warnings during local development checks
    SILENCED_SYSTEM_CHECKS += [
        'security.W004',  # SECURE_HSTS_SECONDS not set
        'security.W008',  # SECURE_SSL_REDIRECT not True
        'security.W012',  # SESSION_COOKIE_SECURE not True
        'security.W016',  # CSRF_COOKIE_SECURE not True
        'security.W018',  # DEBUG True in deployment
    ]
ENABLE_EMAIL_NOTIFICATIONS = env('ENABLE_EMAIL_NOTIFICATIONS', default=True)

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB

# ===========================
# TWO-FACTOR AUTHENTICATION
# ===========================
OTP_TOTP_ISSUER = 'ZAIN HMS - Unified Hospital Management System'
OTP_LOGIN_URL = '/auth/login/'

# ===========================
# DATABASE BACKUP SETTINGS
# ===========================
DBBACKUP_STORAGE = 'django.core.files.storage.FileSystemStorage'
DBBACKUP_STORAGE_OPTIONS = {'location': BASE_DIR / 'backups'}
DBBACKUP_CLEANUP_KEEP = 30  # Keep last 30 backups
DBBACKUP_CLEANUP_KEEP_MEDIA = 30

# ===========================
# HEALTH CHECK SETTINGS
# ===========================
HEALTH_CHECK = {
    'DISK_USAGE_MAX': 90,  # Fail if disk usage is over 90%
    'MEMORY_MIN': 100,     # Fail if available memory is under 100 MB
}

# ===========================
# RATE LIMITING SETTINGS
# ===========================
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'

# ===========================
# ENHANCED SECURITY SETTINGS
# ===========================
# Account lockout settings
LOGIN_ATTEMPT_LIMIT = 5
LOGIN_ATTEMPT_TIMEOUT = 300  # 5 minutes

# Session security
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True

# CSRF settings
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'
CSRF_FAILURE_VIEW = 'apps.core.views.csrf_failure'

# Content Security Policy
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net", "https://cdnjs.cloudflare.com")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net", "https://cdnjs.cloudflare.com", "https://fonts.googleapis.com")
CSP_FONT_SRC = ("'self'", "data:", "https://fonts.gstatic.com", "https://cdn.jsdelivr.net", "https://cdnjs.cloudflare.com")
CSP_IMG_SRC = ("'self'", "data:", "https:")

# Error monitoring (optional)
if env('SENTRY_DSN', default=None):
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    
    sentry_sdk.init(
        dsn=env('SENTRY_DSN'),
        integrations=[
            DjangoIntegration(auto_enabling=True),
            CeleryIntegration(auto_enabling=True),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,
    )

# ===========================


# =============================================================================
# CUSTOM DJANGO ADMIN CONFIGURATION
# =============================================================================

# Django Admin Customization
ADMIN_SITE_HEADER = 'ZAIN HMS - Hospital Management System'
ADMIN_SITE_TITLE = 'ZAIN HMS Admin'
ADMIN_INDEX_TITLE = 'Hospital Dashboard'

# Custom Admin Settings  
ADMIN_SHOW_FULL_RESULT_COUNT = False
ADMIN_REORDER_APPS = True

# PRODUCTION ENVIRONMENT CONFIGURATION
# Load additional production settings if ENVIRONMENT=production
ENVIRONMENT = env('ENVIRONMENT', default='development')

if ENVIRONMENT == 'production':
    # Production-specific imports
    import logging.config
    import secrets
    
    # SECURITY OVERRIDES FOR PRODUCTION
    DEBUG = False
    SECRET_KEY = env('SECRET_KEY', default=secrets.token_urlsafe(50))
    ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')  # Required in production
    
    # HTTPS SECURITY - Healthcare Grade
    SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=True)
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_TLS = True
    
    # HSTS (HTTP Strict Transport Security) - Healthcare grade
    SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=31536000)  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Enhanced Security Headers
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
    SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
    
    # Session Security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_AGE = env.int('SESSION_COOKIE_AGE', default=3600)  # 1 hour default
    SESSION_EXPIRE_AT_BROWSER_CLOSE = True
    
    # Enhanced CSRF Protection
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True
    CSRF_COOKIE_SAMESITE = 'Lax'
    
    # Content Security Policy - Healthcare Grade
    CSP_DEFAULT_SRC = ["'self'"]
    CSP_SCRIPT_SRC = [
        "'self'",
        "https://cdn.jsdelivr.net",
        "https://cdnjs.cloudflare.com",
        "https://unpkg.com",
    ]
    CSP_STYLE_SRC = [
        "'self'",
        "'unsafe-inline'",
        "https://cdn.jsdelivr.net",
        "https://cdnjs.cloudflare.com",
    ]
    CSP_IMG_SRC = ["'self'", "data:", "https:"]
    CSP_FONT_SRC = ["'self'", "https://cdn.jsdelivr.net", "https://cdnjs.cloudflare.com"]
    
    # Enhanced Cache Configuration (Redis for production)
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': env('REDIS_CACHE_URL', default='redis://127.0.0.1:6379/1'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
                'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 50,
                    'retry_on_timeout': True,
                },
            },
            'KEY_PREFIX': 'zain_hms',
            'TIMEOUT': 300,  # 5 minutes default
        },
        'sessions': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': env('REDIS_CACHE_URL', default='redis://127.0.0.1:6379/2'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            },
            'KEY_PREFIX': 'sessions',
            'TIMEOUT': 3600,  # 1 hour
        },
        'locks': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': env('REDIS_CACHE_URL', default='redis://127.0.0.1:6379/3'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            },
            'KEY_PREFIX': 'locks',
            'TIMEOUT': 300,
        }
    }
    
    # Use Redis for sessions (performance + security)
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'sessions'
    
    # Production Database optimization
    DATABASES['default'].update({
        'CONN_MAX_AGE': 60,
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'isolation_level': None,
        }
    })
    
    # Static Files with WhiteNoise optimization
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    WHITENOISE_USE_FINDERS = True
    WHITENOISE_AUTOREFRESH = False  # Disabled in production
    
    # Enhanced Password Validation for Production
    AUTH_PASSWORD_VALIDATORS = [
        {
            'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
            'OPTIONS': {
                'min_length': 12,  # Healthcare grade - 12 chars minimum
            }
        },
        {
            'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
        },
    ]
    
    # Production Email Configuration
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
    EMAIL_PORT = env.int('EMAIL_PORT', default=587)
    EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
    EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
    EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
    DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@zainhms.com')
    
    # Error email notifications
    ADMINS = [
        ('Admin', env('ADMIN_EMAIL', default='admin@zainhms.com')),
    ]
    SERVER_EMAIL = DEFAULT_FROM_EMAIL
    
    # Enhanced Production Logging
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
                'style': '{',
            },
            'simple': {
                'format': '{levelname} {message}',
                'style': '{',
            },
        },
        'filters': {
            'require_debug_false': {
                '()': 'django.utils.log.RequireDebugFalse',
            },
        },
        'handlers': {
            'file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': BASE_DIR / 'logs' / 'django.log',
                'maxBytes': 1024*1024*15,  # 15MB
                'backupCount': 10,
                'formatter': 'verbose',
            },
            'file_auth': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': BASE_DIR / 'logs' / 'authentication.log',
                'maxBytes': 1024*1024*10,  # 10MB
                'backupCount': 5,
                'formatter': 'verbose',
            },
            'file_security': {
                'level': 'WARNING',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': BASE_DIR / 'logs' / 'security.log',
                'maxBytes': 1024*1024*5,  # 5MB
                'backupCount': 5,
                'formatter': 'verbose',
                'filters': ['require_debug_false'],
            },
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'simple'
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
                'handlers': ['file_security'],
                'level': 'WARNING',
                'propagate': False,
            },
            'apps.accounts': {
                'handlers': ['file_auth'],
                'level': 'INFO',
                'propagate': False,
            },
            'apps': {
                'handlers': ['console', 'file'],
                'level': 'INFO',
                'propagate': False,
            },
        },
    }
    
    # Sentry Configuration for Error Monitoring
    SENTRY_DSN = env('SENTRY_DSN', default=None)
    if SENTRY_DSN:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
        from sentry_sdk.integrations.celery import CeleryIntegration
        
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[
                DjangoIntegration(auto_enabling=True),
                CeleryIntegration(monitor_beat_tasks=True),
            ],
            traces_sample_rate=0.1,
            send_default_pii=False,  # Healthcare compliance
            environment='production',
        )


