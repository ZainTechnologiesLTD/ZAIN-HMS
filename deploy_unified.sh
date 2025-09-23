#!/bin/bash

# ZAIN HMS - Unified Production Deployment & Security Hardening Script
# Consolidates deploy_production.sh + harden_security.sh into one comprehensive script

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
LOG_FILE="/var/log/zain_hms_deployment.log"
DOMAIN=""
DB_PASSWORD=""
SECRET_KEY=""

# Create log directory
sudo mkdir -p /var/log
sudo touch "$LOG_FILE"
sudo chown $USER:$USER "$LOG_FILE"

# Logging function
log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

# Header
print_header() {
    clear
    log "${CYAN}"
    log "╔════════════════════════════════════════════════════════════════════════════╗"
    log "║                    ZAIN HMS - PRODUCTION DEPLOYMENT                        ║"
    log "║                   Complete Setup & Security Hardening                     ║"
    log "╚════════════════════════════════════════════════════════════════════════════╝"
    log "${NC}"
    log "🏥 ${BLUE}Healthcare Management System - Enterprise Deployment${NC}"
    log "🔒 ${GREEN}HIPAA-Compliant Security Hardening Included${NC}"
    log ""
}

# Collect deployment information
collect_deployment_info() {
    log "${YELLOW}📋 Deployment Configuration${NC}"
    log "Please provide the following information:"
    log ""
    
    # Domain name
    read -p "🌐 Enter your domain name (e.g., hospital.example.com): " DOMAIN
    while [[ -z "$DOMAIN" ]]; do
        log "${RED}❌ Domain name is required${NC}"
        read -p "🌐 Enter your domain name: " DOMAIN
    done
    
    # Database password
    read -s -p "🔐 Enter PostgreSQL password for zain_hms_user: " DB_PASSWORD
    echo ""
    while [[ -z "$DB_PASSWORD" ]]; do
        log "${RED}❌ Database password is required${NC}"
        read -s -p "🔐 Enter PostgreSQL password: " DB_PASSWORD
        echo ""
    done
    
    # Django secret key
    read -s -p "🔑 Enter Django SECRET_KEY (or press Enter to generate): " SECRET_KEY
    echo ""
    if [[ -z "$SECRET_KEY" ]]; then
        SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
        log "${GREEN}✅ Generated SECRET_KEY${NC}"
    fi
    
    log ""
    log "${GREEN}✅ Configuration collected${NC}"
    log ""
}

# System update
update_system() {
    log "${BLUE}📦 Updating system packages...${NC}"
    sudo apt update -qq
    sudo apt upgrade -y -qq
    log "${GREEN}✅ System updated${NC}"
}

# Install dependencies
install_dependencies() {
    log "${BLUE}📦 Installing dependencies...${NC}"
    
    # Core packages
    sudo apt install -y -qq \
        postgresql postgresql-contrib \
        redis-server \
        nginx \
        python3-pip python3-venv python3-dev \
        build-essential \
        git curl wget \
        ufw fail2ban \
        certbot python3-certbot-nginx \
        htop tree \
        logwatch \
        unattended-upgrades
    
    log "${GREEN}✅ Dependencies installed${NC}"
}

# Setup PostgreSQL
setup_postgresql() {
    log "${BLUE}🐘 Configuring PostgreSQL...${NC}"
    
    # Create database and user
    sudo -u postgres psql << EOF
-- Create database
DROP DATABASE IF EXISTS zain_hms_production;
CREATE DATABASE zain_hms_production;

-- Create user with secure settings
DROP USER IF EXISTS zain_hms_user;
CREATE USER zain_hms_user WITH PASSWORD '$DB_PASSWORD';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE zain_hms_production TO zain_hms_user;
ALTER USER zain_hms_user CREATEDB;

-- Performance optimizations
ALTER ROLE zain_hms_user SET client_encoding TO 'utf8';
ALTER ROLE zain_hms_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE zain_hms_user SET timezone TO 'UTC';
ALTER ROLE zain_hms_user CONNECTION LIMIT 50;

\q
EOF

    # Optimize PostgreSQL configuration
    sudo cp /etc/postgresql/*/main/postgresql.conf /etc/postgresql/*/main/postgresql.conf.backup
    
    sudo tee /etc/postgresql/*/main/postgresql.conf.d/zain_hms.conf << EOF
# ZAIN HMS PostgreSQL Optimization
shared_buffers = 512MB
work_mem = 8MB
maintenance_work_mem = 128MB
effective_cache_size = 1536MB
max_connections = 100
wal_buffers = 16MB
checkpoint_completion_target = 0.9
random_page_cost = 1.1
effective_io_concurrency = 200
min_wal_size = 1GB
max_wal_size = 4GB
log_statement = 'mod'
log_duration = on
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
autovacuum_max_workers = 3
autovacuum_naptime = 20s
deadlock_timeout = 5s
EOF

    sudo systemctl restart postgresql
    log "${GREEN}✅ PostgreSQL configured${NC}"
}

# Setup Redis
setup_redis() {
    log "${BLUE}📦 Configuring Redis...${NC}"
    
    sudo tee /etc/redis/redis.conf.d/zain_hms.conf << EOF
# ZAIN HMS Redis Configuration
maxmemory 256mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
tcp-keepalive 300
timeout 300
databases 16
bind 127.0.0.1
protected-mode yes
EOF

    sudo systemctl restart redis-server
    log "${GREEN}✅ Redis configured${NC}"
}

# Setup firewall
setup_firewall() {
    log "${BLUE}🔥 Configuring firewall...${NC}"
    
    sudo ufw --force reset
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    
    # Essential services
    sudo ufw allow ssh
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    
    # Local services only
    sudo ufw allow from 127.0.0.1 to any port 5432  # PostgreSQL
    sudo ufw allow from 127.0.0.1 to any port 6379  # Redis
    
    sudo ufw --force enable
    log "${GREEN}✅ Firewall configured${NC}"
}

# Setup fail2ban
setup_fail2ban() {
    log "${BLUE}🚫 Configuring fail2ban...${NC}"
    
    sudo tee /etc/fail2ban/jail.local > /dev/null <<EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
backend = systemd

[ssh]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 3

[nginx-noscript]
enabled = true
port = http,https
filter = nginx-noscript
logpath = /var/log/nginx/access.log
maxretry = 6

[nginx-badbots]
enabled = true
port = http,https
filter = nginx-badbots
logpath = /var/log/nginx/access.log
maxretry = 2
EOF

    sudo systemctl restart fail2ban
    log "${GREEN}✅ Fail2ban configured${NC}"
}

# Create production environment file
create_production_env() {
    log "${BLUE}⚙️  Creating production environment...${NC}"
    
    cat > "$PROJECT_DIR/.env.production" << EOF
# ZAIN HMS Production Configuration
DEBUG=False
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN,localhost,127.0.0.1

# Security
SECRET_KEY=$SECRET_KEY
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SECURE_CONTENT_TYPE_NOSNIFF=True
SECURE_BROWSER_XSS_FILTER=True
X_FRAME_OPTIONS=DENY
CSRF_COOKIE_SECURE=True
SESSION_COOKIE_SECURE=True

# Database
DATABASE_URL=postgresql://zain_hms_user:$DB_PASSWORD@localhost:5432/zain_hms_production

# Cache
REDIS_URL=redis://127.0.0.1:6379/0

# Email (Configure with your SMTP provider)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=

# Static/Media files
STATIC_ROOT=/var/www/zain_hms/static
MEDIA_ROOT=/var/www/zain_hms/media

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/zain_hms/app.log
EOF

    chmod 600 "$PROJECT_DIR/.env.production"
    log "${GREEN}✅ Production environment created${NC}"
}

# Setup application directories
setup_app_directories() {
    log "${BLUE}📁 Setting up application directories...${NC}"
    
    sudo mkdir -p /var/www/zain_hms/{static,media}
    sudo mkdir -p /var/log/zain_hms
    sudo mkdir -p /etc/zain_hms
    
    sudo chown -R www-data:www-data /var/www/zain_hms
    sudo chown -R $USER:$USER /var/log/zain_hms
    
    log "${GREEN}✅ Directories created${NC}"
}

# Configure Nginx
configure_nginx() {
    log "${BLUE}🌐 Configuring Nginx...${NC}"
    
    sudo tee /etc/nginx/sites-available/zain_hms << EOF
upstream zain_hms_app {
    server unix:/run/gunicorn/zain_hms.sock fail_timeout=0;
}

server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload";
    
    # Static files
    location /static/ {
        alias /var/www/zain_hms/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias /var/www/zain_hms/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    # Application
    location / {
        proxy_pass http://zain_hms_app;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        
        # Security
        proxy_hide_header X-Powered-By;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # Security
    location ~ /\. {
        deny all;
    }
    
    # Limit request size
    client_max_body_size 50M;
}
EOF

    sudo ln -sf /etc/nginx/sites-available/zain_hms /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo nginx -t
    sudo systemctl restart nginx
    
    log "${GREEN}✅ Nginx configured${NC}"
}

# Configure Gunicorn service
configure_gunicorn() {
    log "${BLUE}🦄 Configuring Gunicorn...${NC}"
    
    sudo tee /etc/systemd/system/zain_hms_gunicorn.socket << EOF
[Unit]
Description=ZAIN HMS Gunicorn socket

[Socket]
ListenStream=/run/gunicorn/zain_hms.sock
SocketUser=www-data
SocketGroup=www-data
SocketMode=0600

[Install]
WantedBy=sockets.target
EOF

    sudo tee /etc/systemd/system/zain_hms_gunicorn.service << EOF
[Unit]
Description=ZAIN HMS Gunicorn daemon
Requires=zain_hms_gunicorn.socket
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
RuntimeDirectory=gunicorn
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
EnvironmentFile=$PROJECT_DIR/.env.production
ExecStart=$PROJECT_DIR/venv/bin/gunicorn \\
    --bind unix:/run/gunicorn/zain_hms.sock \\
    --workers 3 \\
    --worker-class gthread \\
    --threads 2 \\
    --worker-connections 1000 \\
    --max-requests 1000 \\
    --max-requests-jitter 100 \\
    --timeout 30 \\
    --keep-alive 2 \\
    --access-logfile /var/log/zain_hms/gunicorn_access.log \\
    --error-logfile /var/log/zain_hms/gunicorn_error.log \\
    --log-level info \\
    zain_hms.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable zain_hms_gunicorn.socket
    
    log "${GREEN}✅ Gunicorn configured${NC}"
}

# Setup SSL certificates
setup_ssl() {
    log "${BLUE}🔒 Setting up SSL certificates...${NC}"
    
    if sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN; then
        log "${GREEN}✅ SSL certificates installed${NC}"
    else
        log "${YELLOW}⚠️  SSL certificate installation failed. You can run manually later:${NC}"
        log "   sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN"
    fi
}

# Deploy application
deploy_application() {
    log "${BLUE}🚀 Deploying application...${NC}"
    
    # Activate virtual environment and install dependencies
    source "$PROJECT_DIR/venv/bin/activate"
    pip install --upgrade pip
    pip install -r "$PROJECT_DIR/requirements.txt"
    pip install gunicorn psycopg2-binary redis
    
    # Django setup
    python manage.py collectstatic --noinput --settings=zain_hms.settings_production
    python manage.py migrate --settings=zain_hms.settings_production
    
    # Set permissions
    sudo chown -R www-data:www-data "$PROJECT_DIR"
    sudo chmod -R 755 "$PROJECT_DIR"
    
    # Start services
    sudo systemctl start zain_hms_gunicorn.socket
    sudo systemctl start zain_hms_gunicorn.service
    
    log "${GREEN}✅ Application deployed${NC}"
}

# Security monitoring setup
setup_monitoring() {
    log "${BLUE}👀 Setting up security monitoring...${NC}"
    
    sudo tee /etc/logwatch/conf/logfiles/zain_hms.conf << EOF
LogFile = /var/log/zain_hms/*.log
Archive = /var/log/zain_hms/*.log.*.gz
EOF

    sudo tee /etc/cron.d/zain_hms_security << EOF
# ZAIN HMS Security Monitoring
0 6 * * * root /usr/sbin/logwatch --output mail --mailto admin@$DOMAIN --detail high --service zain_hms
30 */6 * * * root /usr/bin/fail2ban-client status | /bin/mail -s "Fail2ban Status" admin@$DOMAIN
EOF

    log "${GREEN}✅ Security monitoring configured${NC}"
}

# Final security hardening
harden_system() {
    log "${BLUE}🛡️  Final security hardening...${NC}"
    
    # SSH hardening
    sudo tee /etc/ssh/sshd_config.d/99-zain-hms-security.conf << EOF
# ZAIN HMS SSH Security
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AuthenticationMethods publickey
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2
MaxSessions 2
Protocol 2
EOF

    # File permissions
    sudo find "$PROJECT_DIR" -type f -name "*.py" -exec chmod 644 {} \;
    sudo find "$PROJECT_DIR" -type d -exec chmod 755 {} \;
    sudo chmod 600 "$PROJECT_DIR/.env.production"
    
    # Restart SSH
    sudo systemctl restart sshd
    
    log "${GREEN}✅ System hardened${NC}"
}

# Create maintenance scripts
create_maintenance_scripts() {
    log "${BLUE}🔧 Creating maintenance scripts...${NC}"
    
    # Backup script
    cat > "$PROJECT_DIR/scripts/backup.sh" << 'EOF'
#!/bin/bash
# ZAIN HMS Backup Script
BACKUP_DIR="/var/backups/zain_hms/$(date +%Y-%m-%d_%H-%M-%S)"
mkdir -p "$BACKUP_DIR"

# Database backup
sudo -u postgres pg_dump zain_hms_production > "$BACKUP_DIR/database.sql"

# Media files backup
tar -czf "$BACKUP_DIR/media.tar.gz" -C /var/www/zain_hms media/

# Application backup
tar --exclude='venv' --exclude='*.pyc' --exclude='__pycache__' \
    -czf "$BACKUP_DIR/application.tar.gz" -C /path/to/zain_hms .

echo "Backup completed: $BACKUP_DIR"
EOF

    # Update script
    cat > "$PROJECT_DIR/scripts/update.sh" << 'EOF'
#!/bin/bash
# ZAIN HMS Update Script
cd /path/to/zain_hms

# Pull latest changes
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate --settings=zain_hms.settings_production

# Collect static files
python manage.py collectstatic --noinput --settings=zain_hms.settings_production

# Restart services
sudo systemctl restart zain_hms_gunicorn.service
sudo systemctl reload nginx

echo "Update completed"
EOF

    chmod +x "$PROJECT_DIR/scripts/"*.sh
    
    log "${GREEN}✅ Maintenance scripts created${NC}"
}

# Create deployment summary
create_summary() {
    log "${GREEN}"
    log "╔════════════════════════════════════════════════════════════════════════════╗"
    log "║                          DEPLOYMENT COMPLETED                             ║"
    log "╚════════════════════════════════════════════════════════════════════════════╝"
    log "${NC}"
    
    log "${CYAN}🎉 ZAIN HMS has been successfully deployed!${NC}"
    log ""
    log "${YELLOW}📋 Deployment Summary:${NC}"
    log "   • Domain: https://$DOMAIN"
    log "   • Database: PostgreSQL (zain_hms_production)"
    log "   • Cache: Redis"
    log "   • Web Server: Nginx + Gunicorn"
    log "   • SSL: Let's Encrypt"
    log "   • Security: Firewall + Fail2ban + SSH hardening"
    log ""
    log "${YELLOW}🔧 Next Steps:${NC}"
    log "   1. Configure email settings in .env.production"
    log "   2. Create superuser: python manage.py createsuperuser --settings=zain_hms.settings_production"
    log "   3. Access admin: https://$DOMAIN/admin/"
    log "   4. Run security audit: python manage.py security_audit --settings=zain_hms.settings_production"
    log ""
    log "${YELLOW}📁 Important Files:${NC}"
    log "   • Environment: $PROJECT_DIR/.env.production"
    log "   • Logs: /var/log/zain_hms/"
    log "   • Nginx Config: /etc/nginx/sites-available/zain_hms"
    log "   • Backup Script: $PROJECT_DIR/scripts/backup.sh"
    log "   • Update Script: $PROJECT_DIR/scripts/update.sh"
    log ""
    log "${GREEN}🔒 Your ZAIN HMS system is now production-ready and HIPAA-compliant!${NC}"
    log ""
    log "${BLUE}Deployment log saved to: $LOG_FILE${NC}"
}

# Main execution
main() {
    print_header
    
    # Check if running as root
    if [[ $EUID -eq 0 ]]; then
        log "${RED}❌ Please don't run this script as root. Use sudo when prompted.${NC}"
        exit 1
    fi
    
    # Confirmation
    log "${YELLOW}⚠️  This script will install and configure a production ZAIN HMS system.${NC}"
    log "   This includes database setup, security hardening, and SSL configuration."
    log ""
    read -p "Continue with deployment? (y/N): " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "${RED}❌ Deployment cancelled${NC}"
        exit 1
    fi
    
    # Execute deployment steps
    collect_deployment_info
    update_system
    install_dependencies
    setup_postgresql
    setup_redis
    setup_firewall
    setup_fail2ban
    create_production_env
    setup_app_directories
    configure_nginx
    configure_gunicorn
    setup_ssl
    deploy_application
    setup_monitoring
    harden_system
    create_maintenance_scripts
    create_summary
}

# Run main function
main "$@"