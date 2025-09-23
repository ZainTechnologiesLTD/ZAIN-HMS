#!/bin/bash
# ZAIN HMS - Production Server Setup Script
# Ubuntu 20.04/22.04 LTS Server Configuration
# Run as root or with sudo privileges

set -e

echo "🏥 ZAIN HMS - Production Server Setup"
echo "===================================="
echo "Setting up Ubuntu server for hospital management system..."

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root"
   echo "Usage: sudo bash setup_server.sh"
   exit 1
fi

# Configuration variables
DOMAIN_NAME="${1:-zain-hms.local}"
DB_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)
SECRET_KEY=$(openssl rand -base64 50)

print_header "System Update & Basic Packages"
apt update && apt upgrade -y
apt install -y curl wget git unzip software-properties-common \
    build-essential python3-pip python3-venv python3-dev \
    postgresql postgresql-contrib redis-server nginx \
    certbot python3-certbot-nginx supervisor htop tree

print_header "Docker Installation"
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl enable docker
systemctl start docker

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

print_status "Docker installed successfully"

print_header "PostgreSQL Database Setup"
# Configure PostgreSQL
systemctl start postgresql
systemctl enable postgresql

# Create database and user
sudo -u postgres createuser --no-createdb --no-createrole --no-superuser zain_hms || true
sudo -u postgres createdb zain_hms_db || true
sudo -u postgres psql -c "ALTER USER zain_hms PASSWORD '$DB_PASSWORD';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE zain_hms_db TO zain_hms;"

# Configure PostgreSQL for better performance
sed -i "s/#max_connections = 100/max_connections = 200/g" /etc/postgresql/*/main/postgresql.conf
sed -i "s/#shared_buffers = 128MB/shared_buffers = 256MB/g" /etc/postgresql/*/main/postgresql.conf
sed -i "s/#effective_cache_size = 4GB/effective_cache_size = 1GB/g" /etc/postgresql/*/main/postgresql.conf

systemctl restart postgresql
print_status "PostgreSQL configured successfully"

print_header "Redis Configuration"
# Configure Redis
sed -i 's/# requirepass foobared/requirepass '$REDIS_PASSWORD'/g' /etc/redis/redis.conf
sed -i 's/# maxmemory <bytes>/maxmemory 256mb/g' /etc/redis/redis.conf
sed -i 's/# maxmemory-policy noeviction/maxmemory-policy allkeys-lru/g' /etc/redis/redis.conf

systemctl restart redis-server
systemctl enable redis-server
print_status "Redis configured successfully"

print_header "Nginx Configuration"
# Remove default nginx site
rm -f /etc/nginx/sites-enabled/default

# Create ZAIN HMS nginx configuration
cat > /etc/nginx/sites-available/zain_hms << EOF
upstream django {
    server unix:///var/www/zain_hms/zain_hms.sock;
}

server {
    listen 80;
    server_name $DOMAIN_NAME www.$DOMAIN_NAME;
    
    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN_NAME www.$DOMAIN_NAME;

    # SSL configuration (will be configured by certbot)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Upload size limit for medical files
    client_max_body_size 100M;
    
    # Main application
    location / {
        uwsgi_pass django;
        include /etc/nginx/uwsgi_params;
        uwsgi_read_timeout 300s;
        uwsgi_send_timeout 300s;
    }

    # Static files
    location /static/ {
        alias /var/www/zain_hms/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files (patient data, secure)
    location /media/ {
        alias /var/www/zain_hms/media/;
        expires 1d;
        add_header Cache-Control "private";
    }
    
    # Health check endpoint
    location /health/ {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

# Enable the site
ln -sf /etc/nginx/sites-available/zain_hms /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
systemctl enable nginx

print_status "Nginx configured successfully"

print_header "Application Directory Setup"
# Create application directory
mkdir -p /var/www/zain_hms
chown -R www-data:www-data /var/www/zain_hms

# Create environment file
cat > /var/www/zain_hms/.env << EOF
# ZAIN HMS Production Environment
DEBUG=False
SECRET_KEY=$SECRET_KEY
ALLOWED_HOSTS=$DOMAIN_NAME,www.$DOMAIN_NAME,localhost,127.0.0.1

# Database Configuration
DATABASE_URL=postgresql://zain_hms:$DB_PASSWORD@localhost:5432/zain_hms_db

# Redis Configuration
REDIS_URL=redis://default:$REDIS_PASSWORD@localhost:6379/1

# Email Configuration (Configure with your SMTP settings)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# AWS S3 for file storage (optional)
# AWS_ACCESS_KEY_ID=your-access-key
# AWS_SECRET_ACCESS_KEY=your-secret-key
# AWS_STORAGE_BUCKET_NAME=zain-hms-media

# GitHub Configuration for updates
GITHUB_REPO=Zain-Technologies-22/ZAIN-HMS
GITHUB_TOKEN=your-github-token
EOF

chmod 600 /var/www/zain_hms/.env
chown www-data:www-data /var/www/zain_hms/.env

print_header "SSL Certificate Setup"
# Request SSL certificate (Let's Encrypt)
certbot --nginx -d $DOMAIN_NAME --non-interactive --agree-tos --email admin@$DOMAIN_NAME || print_warning "SSL certificate setup failed. Configure manually."

print_header "Firewall Configuration"
# Configure UFW firewall
ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 'Nginx Full'
ufw allow 5432 # PostgreSQL (local only)

print_header "System Optimization"
# System performance tuning for hospital workloads
cat >> /etc/sysctl.conf << EOF

# Hospital management system optimizations
vm.swappiness=10
net.core.rmem_max=16777216
net.core.wmem_max=16777216
net.ipv4.tcp_rmem=4096 65536 16777216
net.ipv4.tcp_wmem=4096 65536 16777216
EOF

sysctl -p

print_header "Monitoring Setup"
# Install monitoring tools
apt install -y prometheus-node-exporter
systemctl enable prometheus-node-exporter
systemctl start prometheus-node-exporter

# Create log directories
mkdir -p /var/log/zain_hms
chown www-data:www-data /var/log/zain_hms

print_header "Backup Configuration"
# Create backup directory
mkdir -p /backup/zain_hms/{database,media,logs}
chown -R www-data:www-data /backup/zain_hms

# Create backup script
cat > /backup/zain_hms/backup_script.sh << 'EOF'
#!/bin/bash
# ZAIN HMS Backup Script

DATE=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_DIR="/backup/zain_hms"

# Database backup
pg_dump -h localhost -U zain_hms -d zain_hms_db > $BACKUP_DIR/database/zain_hms_db_$DATE.sql

# Media files backup
tar -czf $BACKUP_DIR/media/media_files_$DATE.tar.gz -C /var/www/zain_hms media/

# Application logs backup
tar -czf $BACKUP_DIR/logs/logs_$DATE.tar.gz -C /var/log zain_hms/

# Keep only last 7 days of backups
find $BACKUP_DIR -type f -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /backup/zain_hms/backup_script.sh

# Setup daily backup cron job
echo "0 2 * * * /backup/zain_hms/backup_script.sh >> /var/log/zain_hms/backup.log 2>&1" | crontab -u www-data -

print_header "Security Hardening"
# Disable root login via SSH
sed -i 's/#PermitRootLogin yes/PermitRootLogin no/g' /etc/ssh/sshd_config
sed -i 's/PermitRootLogin yes/PermitRootLogin no/g' /etc/ssh/sshd_config
systemctl restart ssh

# Install fail2ban
apt install -y fail2ban
systemctl enable fail2ban
systemctl start fail2ban

print_header "Setup Summary"
echo -e "${GREEN}✅ Server setup completed successfully!${NC}\n"
echo "📋 Configuration Summary:"
echo "========================="
echo "Domain: $DOMAIN_NAME"
echo "Database: PostgreSQL (zain_hms_db)"
echo "Cache: Redis with password protection"
echo "Web Server: Nginx with SSL"
echo "Application Directory: /var/www/zain_hms"
echo "Environment File: /var/www/zain_hms/.env"
echo "Backup Directory: /backup/zain_hms"
echo ""
echo "🔐 Important Credentials (SAVE THESE SECURELY):"
echo "=============================================="
echo "Database Password: $DB_PASSWORD"
echo "Redis Password: $REDIS_PASSWORD"
echo "Django Secret Key: $SECRET_KEY"
echo ""
echo "📝 Next Steps:"
echo "=============="
echo "1. Clone your ZAIN HMS repository to /var/www/zain_hms"
echo "2. Configure the environment file with your specific settings"
echo "3. Run the deployment script to deploy your application"
echo "4. Test the installation"
echo ""
print_status "Server is ready for ZAIN HMS deployment!"