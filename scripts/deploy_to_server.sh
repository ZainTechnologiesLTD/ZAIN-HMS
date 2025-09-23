#!/bin/bash
# ZAIN HMS - Server Deployment Script
# Deploy ZAIN HMS to production server

set -e

echo "🏥 ZAIN HMS - Server Deployment"
echo "=============================="

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
APP_DIR="/var/www/zain_hms"
REPO_URL="https://github.com/Zain-Technologies-22/ZAIN-HMS.git"
BRANCH="main"  # Production branch
PYTHON_VERSION="3.9"

print_status "Starting ZAIN HMS deployment..."

# Check if running as root or with sudo
if [[ $EUID -eq 0 ]]; then
    print_warning "Running as root. Switching to www-data user for application setup."
fi

# Navigate to application directory
cd $APP_DIR || { print_error "Application directory not found. Run setup_server.sh first."; exit 1; }

print_status "Cloning ZAIN HMS from GitHub..."
if [ -d ".git" ]; then
    print_status "Repository exists, updating..."
    git fetch origin
    git checkout $BRANCH
    git pull origin $BRANCH
else
    print_status "Cloning fresh repository..."
    git clone -b $BRANCH $REPO_URL .
fi

print_status "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn psycopg2-binary redis

print_status "Installing additional production packages..."
pip install sentry-sdk whitenoise

print_status "Loading environment variables..."
if [ ! -f ".env" ]; then
    print_error "Environment file not found. Please run setup_server.sh first."
    exit 1
fi
set -a
source .env
set +a

print_status "Running database migrations..."
python manage.py migrate --settings=zain_hms.production_settings

print_status "Collecting static files..."
python manage.py collectstatic --noinput --settings=zain_hms.production_settings

print_status "Creating superuser (if needed)..."
python manage.py shell --settings=zain_hms.production_settings << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@zain-hms.com', 'ZainHMS2025!')
    print("Superuser created: admin / ZainHMS2025!")
else:
    print("Superuser already exists")
EOF

print_status "Setting up Gunicorn configuration..."
cat > gunicorn.conf.py << EOF
# Gunicorn configuration for ZAIN HMS
import multiprocessing

# Server socket
bind = "unix:/var/www/zain_hms/zain_hms.sock"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 300
keepalive = 60

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "/var/log/zain_hms/gunicorn_access.log"
errorlog = "/var/log/zain_hms/gunicorn_error.log"
loglevel = "info"

# Process naming
proc_name = "zain_hms"

# Security
limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190

# Performance
preload_app = True
enable_stdio_inheritance = True
EOF

print_status "Setting up Supervisor configuration..."
cat > /etc/supervisor/conf.d/zain_hms.conf << EOF
[program:zain_hms]
directory=/var/www/zain_hms
command=/var/www/zain_hms/venv/bin/gunicorn --config gunicorn.conf.py zain_hms.wsgi:application
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/zain_hms/application.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=5
environment=DJANGO_SETTINGS_MODULE=zain_hms.production_settings

[program:zain_hms_celery]
directory=/var/www/zain_hms
command=/var/www/zain_hms/venv/bin/celery -A zain_hms worker -l info
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/zain_hms/celery.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=5
environment=DJANGO_SETTINGS_MODULE=zain_hms.production_settings

[program:zain_hms_celery_beat]
directory=/var/www/zain_hms
command=/var/www/zain_hms/venv/bin/celery -A zain_hms beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/zain_hms/celery_beat.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=5
environment=DJANGO_SETTINGS_MODULE=zain_hms.production_settings
EOF

print_status "Setting correct permissions..."
chown -R www-data:www-data /var/www/zain_hms
chmod -R 755 /var/www/zain_hms
chmod 600 /var/www/zain_hms/.env

print_status "Reloading Supervisor..."
supervisorctl reread
supervisorctl update
supervisorctl restart all

print_status "Testing Nginx configuration..."
nginx -t
systemctl reload nginx

print_status "Running application health check..."
sleep 5
if curl -f http://localhost/health/ > /dev/null 2>&1; then
    print_status "✅ Health check passed!"
else
    print_warning "⚠️  Health check failed. Check logs for issues."
fi

print_status "Setting up log rotation..."
cat > /etc/logrotate.d/zain_hms << EOF
/var/log/zain_hms/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        supervisorctl restart zain_hms
    endscript
}
EOF

print_status "Creating update script..."
cat > /var/www/zain_hms/update.sh << 'EOF'
#!/bin/bash
# ZAIN HMS Update Script
echo "🔄 Updating ZAIN HMS..."

cd /var/www/zain_hms
source venv/bin/activate

# Pull latest changes
git pull origin main

# Install any new dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate --settings=zain_hms.production_settings

# Collect static files
python manage.py collectstatic --noinput --settings=zain_hms.production_settings

# Restart services
supervisorctl restart zain_hms

echo "✅ Update completed!"
EOF

chmod +x /var/www/zain_hms/update.sh

echo ""
echo -e "${GREEN}🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!${NC}"
echo ""
echo "📋 Deployment Summary:"
echo "====================="
echo "Application: /var/www/zain_hms"
echo "Branch: $BRANCH"
echo "Services: Gunicorn + Nginx + PostgreSQL + Redis"
echo "Logs: /var/log/zain_hms/"
echo "Superuser: admin / ZainHMS2025!"
echo ""
echo "🔧 Management Commands:"
echo "====================="
echo "View logs: tail -f /var/log/zain_hms/application.log"
echo "Restart app: supervisorctl restart zain_hms"
echo "Update app: /var/www/zain_hms/update.sh"
echo "Django shell: cd /var/www/zain_hms && source venv/bin/activate && python manage.py shell --settings=zain_hms.production_settings"
echo ""
print_status "🏥 ZAIN HMS is now running in production!"
print_status "Visit your domain to access the hospital management system"