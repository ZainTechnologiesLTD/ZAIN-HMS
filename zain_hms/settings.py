# zain_hms/settings.py
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

# Application definition
INSTALLED_APPS = [
    # Modern Admin Interface
    'jazzmin',
    # 'admin_interface',
    # 'colorfield',
    
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
    
    # Tenant-specific apps
    'apps.tenants',
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
    'apps.notifications',
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
    'apps.core.middleware.AdminLoginRedirectMiddleware',  # Handle admin login redirects
    # 'apps.core.middleware.HospitalContextMiddleware',  # Disabled - Using single hospital approach
    # 'apps.core.middleware.HospitalSelectionMiddleware',  # Disabled - No hospital selection needed
    'apps.core.single_hospital_middleware.SingleHospitalMiddleware',  # Simple single hospital per user
    'django_otp.middleware.OTPMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.core.middleware.ActivityLogMiddleware',
    'apps.core.middleware.SecurityHeadersMiddleware',
    'apps.core.middleware.RateLimitMiddleware',
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
                'apps.core.context_processors.hospital_context',
                'apps.core.context_processors.notifications_context',
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

# Multi-tenant Database Router
DATABASE_ROUTERS = ['apps.core.db_router.MultiTenantDBRouter']

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

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,  # Enhanced from 8 to 12
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

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
SESSION_COOKIE_AGE = 86400  # 24 hours
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
    },
}

# Application Specific Settings
HOSPITAL_NAME = env('HOSPITAL_NAME', default='ZAIN Hospital')
HOSPITAL_CODE = env('HOSPITAL_CODE', default='ZAIN')
CURRENCY_SYMBOL = env('CURRENCY_SYMBOL', default='\\$')
APPOINTMENT_DURATION_MINUTES = 30
MAX_APPOINTMENTS_PER_DAY = 50
ENABLE_SMS_NOTIFICATIONS = env('ENABLE_SMS_NOTIFICATIONS', default=False)

# ===========================
# DJANGO ADMIN INTERFACE SETTINGS  
# ===========================
X_FRAME_OPTIONS = 'SAMEORIGIN'
SILENCED_SYSTEM_CHECKS = ['security.W019']
ENABLE_EMAIL_NOTIFICATIONS = env('ENABLE_EMAIL_NOTIFICATIONS', default=True)

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB

# ===========================
# TWO-FACTOR AUTHENTICATION
# ===========================
OTP_TOTP_ISSUER = 'ZAIN Hospital Management'
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
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net", "https://fonts.googleapis.com")
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com", "https://cdn.jsdelivr.net", "https://cdnjs.cloudflare.com")
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

# Shared and Tenant-specific Apps
SHARED_APPS = [
    'django.contrib.contenttypes',
    'tenants',
    'accounts',
    'django.contrib.auth',
    'django.contrib.sessions',
]

# ===========================
# JAZZMIN ADMIN UI SETTINGS - DEFAULT
# ===========================
# Using Jazzmin default settings for clean, standard admin interface
# Custom settings have been commented out to use Jazzmin defaults

# JAZZMIN_SETTINGS = {
#     # Branding & Identity
#     "site_title": "Zain HMS Administration",
#     "site_header": "Zain Hospital Management System",
#     "site_brand": "Zain HMS",
#     ... (custom settings commented out)
# }

# JAZZMIN_UI_TWEAKS = {
#     # Enhanced Themes
#     "theme": "cosmo",
#     "dark_mode_theme": "darkly",
#     ... (custom UI tweaks commented out)
# }

TENANT_APPS = [
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    # 'admin_interface',
    # 'colorfield',
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'dj_rest_auth',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'django_otp',
    'django_otp.plugins.otp_static',
    'django_otp.plugins.otp_totp',
    'django_celery_beat',
    'django_celery_results',
    'db',
    'apps.core',
    'apps.patients',
    'apps.doctors',
    'apps.nurses',
    'apps.staff',
    'apps.appointments',
    'apps.billing',
    'apps.pharmacy',
    'apps.laboratory',
    'apps.radiology',
    'apps.ipd',
    'apps.opd',
    'apps.emergency',
    'apps.surgery',
    'apps.reports',
    'apps.analytics',
    'apps.inventory',
    'apps.hr',
    'apps.feedback',
    'apps.notifications',
    'apps.contact',
    'apps.telemedicine',
    'apps.dashboard',
    'apps.room_management',
]

