# Production Settings Configuration for Update System
# Add to your settings_production.py or settings.py

"""
Add these settings to your Django configuration for the update system to work properly:

# Version Management
VERSION = '2.1.0'  # Update this with each release

# GitHub Integration (for update checking)
GITHUB_REPO = 'yourusername/zain_hms'  # Replace with your actual GitHub repo
GITHUB_TOKEN = 'your_github_token_here'  # Create a GitHub Personal Access Token

# Update System Configuration
UPDATE_CHECK_ENABLED = True
UPDATE_CHECK_INTERVAL = 6 * 60 * 60  # Check every 6 hours (in seconds)
CRITICAL_UPDATE_NOTIFICATION = True
AUTO_BACKUP_BEFORE_UPDATE = True
BACKUP_RETENTION_DAYS = 30

# Deployment Configuration
DEPLOYMENT_SCRIPT_PATH = '/opt/zain_hms/scripts/deploy.sh'
BACKUP_DIRECTORY = '/opt/zain_hms/backups'
LOG_DIRECTORY = '/opt/zain_hms/logs'

# Notification Settings
SYSTEM_UPDATE_NOTIFICATIONS = True
UPDATE_NOTIFICATION_EMAIL = True
ADMIN_EMAIL_LIST = [
    'admin@zainhms.com',
    'tech@zainhms.com',
]

# Security Settings for Updates
REQUIRE_ADMIN_APPROVAL = True
MAINTENANCE_MODE_DURING_UPDATE = True
HEALTH_CHECK_TIMEOUT = 30
ROLLBACK_ON_FAILURE = True

# Client Notification Settings
CLIENT_NOTIFICATION_ENABLED = True
CLIENT_UPDATE_ANNOUNCEMENT = True
DOWNTIME_NOTIFICATION_MINUTES = 30  # Notify clients 30 minutes before update

# Logging Configuration for Updates
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
    'handlers': {
        'update_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/opt/zain_hms/logs/updates.log',
            'formatter': 'verbose',
        },
        'deployment_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/opt/zain_hms/logs/deployment.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'zain_hms.updates': {
            'handlers': ['update_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'zain_hms.deployment': {
            'handlers': ['deployment_file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
"""

# Development settings override for testing
if DEBUG:
    # Use test repository for development
    GITHUB_REPO = 'test-repo/zain_hms'
    UPDATE_CHECK_ENABLED = False  # Disable in development
    REQUIRE_ADMIN_APPROVAL = False
    MAINTENANCE_MODE_DURING_UPDATE = False