#!/bin/bash
# 🏥 ZAIN HMS Production Server Setup Script
# Prepares Ubuntu server for Docker-based deployment

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
ZAIN_HMS_USER="zain-hms"
APP_DIR="/opt/zain_hms"
DOMAIN="${1:-localhost}"

echo -e "${BLUE}🏥 ZAIN HMS Production Server Setup${NC}"
echo "===================================="
echo "Setting up server for domain: $DOMAIN"
echo ""

# Function to check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}❌ Please run this script as root (use sudo)${NC}"
        exit 1
    fi
}

# Function to update system
update_system() {
    echo -e "${YELLOW}📦 Updating system packages...${NC}"
    apt update && apt upgrade -y
    echo -e "${GREEN}✅ System updated${NC}"
}

# Function to install Docker
install_docker() {
    echo -e "${YELLOW}🐳 Installing Docker...${NC}"
    
    # Remove old Docker versions
    apt remove -y docker docker-engine docker.io containerd runc || true
    
    # Install dependencies
    apt install -y apt-transport-https ca-certificates curl gnupg lsb-release
    
    # Add Docker GPG key
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Add Docker repository
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker
    apt update
    apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Start and enable Docker
    systemctl start docker
    systemctl enable docker
    
    echo -e "${GREEN}✅ Docker installed${NC}"
}

# Function to install Docker Compose
install_docker_compose() {
    echo -e "${YELLOW}🔧 Installing Docker Compose...${NC}"
    
    # Install latest version of Docker Compose
    LATEST_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep tag_name | cut -d '"' -f 4)
    curl -L "https://github.com/docker/compose/releases/download/${LATEST_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    # Create symlink
    ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    
    echo -e "${GREEN}✅ Docker Compose installed${NC}"
}

# Function to create application user
create_app_user() {
    echo -e "${YELLOW}👤 Creating application user...${NC}"
    
    # Create user if it doesn't exist
    if ! id "$ZAIN_HMS_USER" &>/dev/null; then
        useradd -m -s /bin/bash "$ZAIN_HMS_USER"
        usermod -aG docker "$ZAIN_HMS_USER"
        echo -e "${GREEN}✅ User $ZAIN_HMS_USER created${NC}"
    else
        echo -e "${YELLOW}⚠️  User $ZAIN_HMS_USER already exists${NC}"
    fi
}

# Function to setup directory structure
setup_directories() {
    echo -e "${YELLOW}📁 Setting up directory structure...${NC}"
    
    # Create main application directory
    mkdir -p "$APP_DIR"
    mkdir -p "$APP_DIR/data/postgres"
    mkdir -p "$APP_DIR/data/redis"
    mkdir -p "$APP_DIR/data/static"
    mkdir -p "$APP_DIR/data/media"
    mkdir -p "$APP_DIR/logs"
    mkdir -p "$APP_DIR/backups"
    mkdir -p "$APP_DIR/ssl"
    
    # Set ownership
    chown -R "$ZAIN_HMS_USER:$ZAIN_HMS_USER" "$APP_DIR"
    
    # Set permissions
    chmod -R 755 "$APP_DIR"
    chmod -R 700 "$APP_DIR/ssl"
    
    echo -e "${GREEN}✅ Directory structure created${NC}"
}

# Function to install system dependencies
install_system_dependencies() {
    echo -e "${YELLOW}📦 Installing system dependencies...${NC}"
    
    apt install -y \
        nginx \
        ufw \
        fail2ban \
        htop \
        tree \
        git \
        curl \
        wget \
        unzip \
        postgresql-client \
        redis-tools \
        certbot \
        python3-certbot-nginx \
        logrotate \
        rsyslog
    
    echo -e "${GREEN}✅ System dependencies installed${NC}"
}

# Function to configure firewall
configure_firewall() {
    echo -e "${YELLOW}🔥 Configuring firewall...${NC}"
    
    # Reset UFW
    ufw --force reset
    
    # Default policies
    ufw default deny incoming
    ufw default allow outgoing
    
    # Allow SSH (be careful!)
    ufw allow ssh
    
    # Allow HTTP and HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # Allow Docker subnet
    ufw allow from 172.20.0.0/16
    
    # Enable firewall
    ufw --force enable
    
    echo -e "${GREEN}✅ Firewall configured${NC}"
}

# Function to configure fail2ban
configure_fail2ban() {
    echo -e "${YELLOW}🛡️  Configuring Fail2ban...${NC}"
    
    cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
backend = systemd

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
port = http,https
logpath = /var/log/nginx/error.log
EOF
    
    systemctl enable fail2ban
    systemctl restart fail2ban
    
    echo -e "${GREEN}✅ Fail2ban configured${NC}"
}

# Function to setup log rotation
setup_log_rotation() {
    echo -e "${YELLOW}📝 Setting up log rotation...${NC}"
    
    cat > /etc/logrotate.d/zain-hms << EOF
$APP_DIR/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 $ZAIN_HMS_USER $ZAIN_HMS_USER
    postrotate
        docker-compose -f $APP_DIR/docker-compose.prod.yml restart nginx || true
    endscript
}
EOF
    
    echo -e "${GREEN}✅ Log rotation configured${NC}"
}

# Function to create deployment script
create_deployment_script() {
    echo -e "${YELLOW}🚀 Creating deployment script...${NC}"
    
    cat > "$APP_DIR/deploy.sh" << 'EOF'
#!/bin/bash
# ZAIN HMS Deployment Script for Production

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

APP_DIR="/opt/zain_hms"
cd "$APP_DIR"

echo -e "${GREEN}🏥 Starting ZAIN HMS Deployment...${NC}"

# Load environment variables
if [ -f .env.prod ]; then
    export $(cat .env.prod | grep -v '^#' | xargs)
else
    echo -e "${RED}❌ .env.prod file not found!${NC}"
    exit 1
fi

# Create backup
echo -e "${YELLOW}📦 Creating backup...${NC}"
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup database if running
if docker-compose -f docker-compose.prod.yml ps db | grep -q "Up"; then
    docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U "$DB_USER" "$DB_NAME" > "$BACKUP_DIR/database.sql"
    echo -e "${GREEN}✅ Database backup created${NC}"
fi

# Pull latest images
echo -e "${YELLOW}📥 Pulling latest images...${NC}"
docker-compose -f docker-compose.prod.yml pull

# Deploy with zero downtime
echo -e "${YELLOW}🚀 Deploying application...${NC}"
docker-compose -f docker-compose.prod.yml up -d --remove-orphans

# Wait for services
echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
sleep 30

# Health check
if curl -f http://localhost/health/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Deployment successful!${NC}"
else
    echo -e "${RED}❌ Health check failed!${NC}"
    echo "Rolling back..."
    # Add rollback logic here
    exit 1
fi

# Cleanup
docker system prune -f

echo -e "${GREEN}🎉 ZAIN HMS deployed successfully!${NC}"
EOF

    chmod +x "$APP_DIR/deploy.sh"
    chown "$ZAIN_HMS_USER:$ZAIN_HMS_USER" "$APP_DIR/deploy.sh"
    
    echo -e "${GREEN}✅ Deployment script created${NC}"
}

# Function to setup SSL with Let's Encrypt (optional)
setup_ssl() {
    if [ "$DOMAIN" != "localhost" ]; then
        echo -e "${YELLOW}🔒 Setting up SSL certificate...${NC}"
        
        # Stop nginx if running
        systemctl stop nginx || true
        
        # Obtain certificate
        certbot certonly --standalone -d "$DOMAIN" --non-interactive --agree-tos --email admin@"$DOMAIN" || echo "SSL setup failed, continuing..."
        
        echo -e "${GREEN}✅ SSL certificate setup attempted${NC}"
    else
        echo -e "${YELLOW}⚠️  Skipping SSL setup for localhost${NC}"
    fi
}

# Function to create systemd service
create_systemd_service() {
    echo -e "${YELLOW}⚙️  Creating systemd service...${NC}"
    
    cat > /etc/systemd/system/zain-hms.service << EOF
[Unit]
Description=ZAIN HMS Docker Compose Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
User=$ZAIN_HMS_USER
Group=$ZAIN_HMS_USER
WorkingDirectory=$APP_DIR
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable zain-hms
    
    echo -e "${GREEN}✅ Systemd service created${NC}"
}

# Main installation function
main() {
    echo -e "${BLUE}Starting ZAIN HMS production server setup...${NC}"
    
    check_root
    update_system
    install_docker
    install_docker_compose
    create_app_user
    setup_directories
    install_system_dependencies
    configure_firewall
    configure_fail2ban
    setup_log_rotation
    create_deployment_script
    setup_ssl
    create_systemd_service
    
    echo ""
    echo -e "${GREEN}🎉 ZAIN HMS production server setup completed successfully!${NC}"
    echo ""
    echo -e "${YELLOW}📋 Next Steps:${NC}"
    echo "1. Copy your application files to: $APP_DIR"
    echo "2. Create environment file: $APP_DIR/.env.prod"
    echo "3. Run deployment: sudo -u $ZAIN_HMS_USER $APP_DIR/deploy.sh"
    echo ""
    echo -e "${YELLOW}📊 System Information:${NC}"
    echo "• Docker version: $(docker --version)"
    echo "• Docker Compose version: $(docker-compose --version)"
    echo "• Application directory: $APP_DIR"
    echo "• Application user: $ZAIN_HMS_USER"
    echo "• Domain: $DOMAIN"
    echo ""
    echo -e "${GREEN}✅ Server is ready for ZAIN HMS deployment!${NC}"
}

# Run main function
main "$@"