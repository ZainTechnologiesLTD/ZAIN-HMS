#!/bin/bash
# 🏥 ZAIN HMS Offline Installation Package Creator
# Creates a complete offline installation package with all dependencies

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
OFFLINE_DIR="$PROJECT_DIR/offline-installer"
DOCKER_IMAGES_DIR="$OFFLINE_DIR/docker-images"
PACKAGES_DIR="$OFFLINE_DIR/packages"

echo -e "${CYAN}🏥 ZAIN HMS Offline Installer Creator${NC}"
echo "======================================="

# Function to create directory structure
create_structure() {
    echo -e "${YELLOW}📁 Creating offline installer structure...${NC}"
    
    rm -rf "$OFFLINE_DIR"
    mkdir -p "$OFFLINE_DIR"
    mkdir -p "$DOCKER_IMAGES_DIR"
    mkdir -p "$PACKAGES_DIR"
    mkdir -p "$OFFLINE_DIR/scripts"
    mkdir -p "$OFFLINE_DIR/config"
    
    echo -e "${GREEN}✅ Directory structure created${NC}"
}

# Function to export Docker images
export_docker_images() {
    echo -e "${YELLOW}🐳 Exporting Docker images...${NC}"
    
    # List of required images
    local images=(
        "postgres:15-alpine"
        "redis:7-alpine" 
        "nginx:alpine"
        "python:3.12-slim"
    )
    
    for image in "${images[@]}"; do
        echo -e "${BLUE}Pulling and exporting: $image${NC}"
        docker pull "$image"
        
        # Export image
        local image_file=$(echo "$image" | sed 's/[\/:]/_/g')
        docker save "$image" -o "$DOCKER_IMAGES_DIR/${image_file}.tar"
        
        echo -e "${GREEN}✅ Exported: ${image_file}.tar${NC}"
    done
}

# Function to download system packages
download_packages() {
    echo -e "${YELLOW}📦 Downloading system packages...${NC}"
    
    # Create package download script
    cat > "$PACKAGES_DIR/download-packages.sh" << 'EOF'
#!/bin/bash
# Download packages for offline installation

set -e

PACKAGES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to download packages for Ubuntu/Debian
download_deb_packages() {
    echo "Downloading DEB packages..."
    
    # Update package list
    apt update
    
    # Create directory for debs
    mkdir -p "$PACKAGES_DIR/ubuntu"
    cd "$PACKAGES_DIR/ubuntu"
    
    # Download Docker and dependencies
    apt download \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release \
        docker-ce \
        docker-ce-cli \
        containerd.io \
        docker-compose-plugin \
        git \
        unzip \
        tar \
        jq \
        nginx \
        ufw \
        fail2ban \
        htop \
        tree \
        wget \
        postgresql-client \
        redis-tools \
        certbot \
        python3-certbot-nginx \
        logrotate \
        rsyslog \
        2>/dev/null || echo "Some packages may not be available"
    
    echo "✅ DEB packages downloaded"
}

# Function to download packages for CentOS/RHEL
download_rpm_packages() {
    echo "Downloading RPM packages..."
    
    mkdir -p "$PACKAGES_DIR/centos"
    cd "$PACKAGES_DIR/centos"
    
    # Download packages using yumdownloader
    yumdownloader \
        curl \
        wget \
        git \
        unzip \
        tar \
        jq \
        nginx \
        firewalld \
        htop \
        tree \
        postgresql \
        redis \
        2>/dev/null || echo "Some packages may not be available"
    
    echo "✅ RPM packages downloaded"
}

# Detect OS and download appropriate packages
if command -v apt >/dev/null 2>&1; then
    download_deb_packages
elif command -v yum >/dev/null 2>&1; then
    download_rpm_packages
else
    echo "⚠️ Package manager not supported for offline package download"
fi
EOF
    
    chmod +x "$PACKAGES_DIR/download-packages.sh"
    
    # Download Docker Compose binary
    echo -e "${BLUE}Downloading Docker Compose binary...${NC}"
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep tag_name | cut -d '"' -f 4)
    curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o "$PACKAGES_DIR/docker-compose"
    chmod +x "$PACKAGES_DIR/docker-compose"
    
    echo -e "${GREEN}✅ Package download scripts created${NC}"
}

# Function to copy application files
copy_application_files() {
    echo -e "${YELLOW}📋 Copying application files...${NC}"
    
    # Copy essential files
    cp "$PROJECT_DIR/docker-compose.prod.yml" "$OFFLINE_DIR/"
    cp -r "$PROJECT_DIR/docker" "$OFFLINE_DIR/"
    cp -r "$PROJECT_DIR/scripts" "$OFFLINE_DIR/"
    cp "$PROJECT_DIR/.env.production.template" "$OFFLINE_DIR/config/"
    cp "$PROJECT_DIR/requirements.txt" "$OFFLINE_DIR/config/"
    
    # Copy documentation
    mkdir -p "$OFFLINE_DIR/docs"
    cp -r "$PROJECT_DIR/docs"/* "$OFFLINE_DIR/docs/" 2>/dev/null || true
    
    echo -e "${GREEN}✅ Application files copied${NC}"
}

# Function to create offline installer script
create_offline_installer() {
    echo -e "${YELLOW}🛠️  Creating offline installer script...${NC}"
    
    cat > "$OFFLINE_DIR/install-offline.sh" << 'EOF'
#!/bin/bash
# 🏥 ZAIN HMS Offline Installer
# Install ZAIN HMS without internet connection

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
OFFLINE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/opt/zain-hms"
SERVICE_USER="zain-hms"
DOMAIN="${1:-localhost}"

echo -e "${CYAN}🏥 ZAIN HMS Offline Installation${NC}"
echo "=================================="

# Check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}❌ Please run as root: sudo $0${NC}"
        exit 1
    fi
}

# Detect operating system
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VERSION=$VERSION_ID
    else
        echo -e "${RED}❌ Cannot detect operating system${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Detected OS: $OS $VERSION${NC}"
    
    case "$OS" in
        *Ubuntu*|*Debian*)
            PACKAGE_MANAGER="apt"
            PACKAGES_DIR="$OFFLINE_DIR/packages/ubuntu"
            ;;
        *CentOS*|*Red\ Hat*|*Rocky*|*AlmaLinux*)
            PACKAGE_MANAGER="yum"
            PACKAGES_DIR="$OFFLINE_DIR/packages/centos"
            ;;
        *)
            echo -e "${YELLOW}⚠️  OS not officially supported${NC}"
            PACKAGE_MANAGER="apt"
            PACKAGES_DIR="$OFFLINE_DIR/packages/ubuntu"
            ;;
    esac
}

# Install system packages from offline cache
install_offline_packages() {
    echo -e "${YELLOW}📦 Installing system packages from offline cache...${NC}"
    
    if [ -d "$PACKAGES_DIR" ] && [ "$(ls -A "$PACKAGES_DIR")" ]; then
        case "$PACKAGE_MANAGER" in
            apt)
                dpkg -i "$PACKAGES_DIR"/*.deb 2>/dev/null || true
                apt-get install -f -y
                ;;
            yum)
                rpm -ivh "$PACKAGES_DIR"/*.rpm 2>/dev/null || true
                ;;
        esac
        echo -e "${GREEN}✅ Offline packages installed${NC}"
    else
        echo -e "${YELLOW}⚠️  No offline packages found, attempting online installation${NC}"
        
        case "$PACKAGE_MANAGER" in
            apt)
                apt update
                apt install -y curl wget git unzip tar jq
                ;;
            yum)
                yum update -y
                yum install -y curl wget git unzip tar jq
                ;;
        esac
    fi
}

# Install Docker from offline packages or online
install_docker() {
    echo -e "${YELLOW}🐳 Installing Docker...${NC}"
    
    if command -v docker >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Docker already installed${NC}"
        return
    fi
    
    # Try to start Docker service (might be installed but not running)
    systemctl start docker 2>/dev/null || true
    systemctl enable docker 2>/dev/null || true
    
    if command -v docker >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Docker service started${NC}"
        return
    fi
    
    # If Docker not available, try online installation
    echo -e "${YELLOW}Installing Docker from internet...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    
    systemctl start docker
    systemctl enable docker
    
    echo -e "${GREEN}✅ Docker installed${NC}"
}

# Install Docker Compose
install_docker_compose() {
    echo -e "${YELLOW}🔧 Installing Docker Compose...${NC}"
    
    if [ -f "$OFFLINE_DIR/packages/docker-compose" ]; then
        cp "$OFFLINE_DIR/packages/docker-compose" /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
        ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
        echo -e "${GREEN}✅ Docker Compose installed from offline package${NC}"
    else
        echo -e "${YELLOW}Downloading Docker Compose...${NC}"
        COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep tag_name | cut -d '"' -f 4)
        curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
        ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
        echo -e "${GREEN}✅ Docker Compose installed${NC}"
    fi
}

# Load Docker images from offline files
load_docker_images() {
    echo -e "${YELLOW}🐳 Loading Docker images...${NC}"
    
    if [ -d "$OFFLINE_DIR/docker-images" ]; then
        for image_file in "$OFFLINE_DIR/docker-images"/*.tar; do
            if [ -f "$image_file" ]; then
                echo -e "${BLUE}Loading: $(basename "$image_file")${NC}"
                docker load -i "$image_file"
            fi
        done
        echo -e "${GREEN}✅ Docker images loaded${NC}"
    else
        echo -e "${YELLOW}⚠️  No offline images found, will pull from internet${NC}"
    fi
}

# Create application user
create_app_user() {
    echo -e "${YELLOW}👤 Creating application user...${NC}"
    
    if id "$SERVICE_USER" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ User $SERVICE_USER already exists${NC}"
    else
        useradd -m -s /bin/bash "$SERVICE_USER"
        usermod -aG docker "$SERVICE_USER"
        echo -e "${GREEN}✅ User $SERVICE_USER created${NC}"
    fi
}

# Setup application
setup_application() {
    echo -e "${YELLOW}🏥 Setting up ZAIN HMS application...${NC}"
    
    # Create installation directory
    mkdir -p "$INSTALL_DIR"
    
    # Copy application files
    cp -r "$OFFLINE_DIR/docker" "$INSTALL_DIR/"
    cp -r "$OFFLINE_DIR/scripts" "$INSTALL_DIR/"
    cp "$OFFLINE_DIR/docker-compose.prod.yml" "$INSTALL_DIR/"
    
    # Setup data directories
    mkdir -p "$INSTALL_DIR/data"/{postgres,redis,static,media}
    mkdir -p "$INSTALL_DIR"/{logs,backups,ssl}
    
    # Copy and configure environment
    cp "$OFFLINE_DIR/config/.env.production.template" "$INSTALL_DIR/.env.prod"
    
    # Generate secure passwords
    DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    REDIS_PASSWORD=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-20)
    SECRET_KEY=$(openssl rand -base64 75 | tr -d "=+/" | cut -c1-50)
    
    # Update environment file
    sed -i "s/your-very-secure-database-password-123/$DB_PASSWORD/g" "$INSTALL_DIR/.env.prod"
    sed -i "s/your-secure-redis-password-123/$REDIS_PASSWORD/g" "$INSTALL_DIR/.env.prod"
    sed -i "s/your-super-secret-django-key-here-must-be-50-characters-long-and-unique-123456789/$SECRET_KEY/g" "$INSTALL_DIR/.env.prod"
    sed -i "s/yourdomain.com/$DOMAIN/g" "$INSTALL_DIR/.env.prod"
    
    # Set ownership and permissions
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    chmod 600 "$INSTALL_DIR/.env.prod"
    chmod +x "$INSTALL_DIR/scripts"/*.sh
    
    echo -e "${GREEN}✅ Application setup completed${NC}"
}

# Install systemd service
install_systemd_service() {
    echo -e "${YELLOW}⚙️  Installing systemd service...${NC}"
    
    cat > /etc/systemd/system/zain-hms.service << EOSF
[Unit]
Description=ZAIN HMS Hospital Management System
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOSF
    
    systemctl daemon-reload
    systemctl enable zain-hms
    
    echo -e "${GREEN}✅ Systemd service installed${NC}"
}

# Deploy application
deploy_application() {
    echo -e "${YELLOW}🚀 Deploying ZAIN HMS...${NC}"
    
    cd "$INSTALL_DIR"
    
    # Start services
    sudo -u "$SERVICE_USER" docker-compose -f docker-compose.prod.yml up -d
    
    # Wait for services
    echo -e "${YELLOW}⏳ Waiting for services to start...${NC}"
    sleep 30
    
    # Check health
    if curl -f http://localhost/health/ >/dev/null 2>&1; then
        echo -e "${GREEN}✅ ZAIN HMS deployed successfully!${NC}"
    else
        echo -e "${YELLOW}⚠️  Services may still be starting up${NC}"
    fi
}

# Main installation function
main() {
    check_root
    detect_os
    install_offline_packages
    install_docker
    install_docker_compose
    load_docker_images
    create_app_user
    setup_application
    install_systemd_service
    deploy_application
    
    echo ""
    echo -e "${GREEN}🎉 ZAIN HMS Offline Installation Completed! 🎉${NC}"
    echo ""
    echo -e "${CYAN}Access your system at: http://$(hostname -I | awk '{print $1}')${NC}"
    echo -e "${CYAN}Default login: admin / admin123${NC}"
    echo ""
    echo -e "${YELLOW}Management Commands:${NC}"
    echo "  systemctl start zain-hms    # Start services"
    echo "  systemctl stop zain-hms     # Stop services"
    echo "  systemctl status zain-hms   # Check status"
}

# Run installation
main "$@"
EOF
    
    chmod +x "$OFFLINE_DIR/install-offline.sh"
    
    echo -e "${GREEN}✅ Offline installer script created${NC}"
}

# Function to create README for offline installer
create_readme() {
    echo -e "${YELLOW}📝 Creating installation README...${NC}"
    
    cat > "$OFFLINE_DIR/README.md" << 'EOF'
# 🏥 ZAIN HMS Offline Installer Package

**Bismillahir Rahmanir Raheem**

This package contains everything needed to install ZAIN HMS without an internet connection.

## 📦 Package Contents

- `install-offline.sh` - Main offline installer script
- `docker-images/` - Pre-downloaded Docker images
- `packages/` - System packages for offline installation
- `docker/` - Docker configuration files
- `scripts/` - Utility scripts
- `config/` - Configuration templates
- `docs/` - Documentation

## 🚀 Quick Installation

### Prerequisites
- Ubuntu 18.04+ or CentOS 7+ (or compatible Linux distribution)
- Root access (sudo privileges)
- At least 4GB RAM and 20GB disk space

### Installation Steps

1. **Extract the package** (if downloaded as archive):
   ```bash
   tar -xzf zain-hms-offline-installer.tar.gz
   cd zain-hms-offline-installer
   ```

2. **Run the installer**:
   ```bash
   sudo ./install-offline.sh
   ```

3. **With custom domain** (optional):
   ```bash
   sudo ./install-offline.sh yourdomain.com
   ```

### Installation Process

The installer will:
1. ✅ Check system requirements
2. 📦 Install system packages from offline cache
3. 🐳 Install Docker and Docker Compose
4. 📥 Load Docker images from offline files
5. 👤 Create application user
6. 🏥 Setup ZAIN HMS application
7. ⚙️ Install systemd service
8. 🚀 Deploy and start services

## 🌐 Accessing ZAIN HMS

After installation:

- **Web Interface**: `http://YOUR_SERVER_IP`
- **Admin Panel**: `http://YOUR_SERVER_IP/admin/`
- **Default Login**: `admin` / `admin123`

## 🔧 Management Commands

```bash
# Start services
sudo systemctl start zain-hms

# Stop services
sudo systemctl stop zain-hms

# Check status
sudo systemctl status zain-hms

# View logs
sudo docker-compose -f /opt/zain-hms/docker-compose.prod.yml logs -f

# Restart services
sudo systemctl restart zain-hms
```

## 🔒 Security Notes

1. **Change default password** immediately after first login
2. **Configure firewall** to allow only necessary ports (80, 443, 22)
3. **Setup SSL certificate** for production use
4. **Regular backups** - data is stored in `/opt/zain-hms/data/`

## 📚 Documentation

- Full documentation is available in the `docs/` directory
- Online documentation: https://github.com/Zain-Technologies-22/ZAIN-HMS

## 🆘 Troubleshooting

### Common Issues

1. **Docker not starting**:
   ```bash
   sudo systemctl start docker
   sudo systemctl enable docker
   ```

2. **Permission denied**:
   ```bash
   sudo chown -R zain-hms:zain-hms /opt/zain-hms
   ```

3. **Port already in use**:
   ```bash
   sudo netstat -tulpn | grep :80
   sudo systemctl stop nginx  # If nginx is running
   ```

4. **Services not responding**:
   ```bash
   cd /opt/zain-hms
   sudo docker-compose -f docker-compose.prod.yml restart
   ```

### Log Files

- Application logs: `/opt/zain-hms/logs/`
- Docker logs: `sudo docker-compose logs`
- System logs: `/var/log/syslog`

## 📞 Support

- **Issues**: https://github.com/ZainTechnologiesLTD/ZAIN-HMS/issues
- **Documentation**: https://github.com/ZainTechnologiesLTD/ZAIN-HMS/wiki
- **Email**: support@zainhms.com

## 🎯 System Requirements

### Minimum Requirements
- **OS**: Ubuntu 18.04+ / CentOS 7+ / Debian 9+
- **RAM**: 2GB (4GB recommended)
- **Disk**: 20GB (50GB recommended)
- **CPU**: 2 cores (4 cores recommended)

### Production Requirements
- **OS**: Ubuntu 20.04 LTS / CentOS 8+
- **RAM**: 8GB+
- **Disk**: 100GB+ SSD
- **CPU**: 4+ cores
- **Network**: Static IP, domain name, SSL certificate

## 📋 Package Information

- **Version**: Latest
- **Build Date**: $(date)
- **Package Size**: ~2GB (includes all dependencies)
- **Supported OS**: Ubuntu, Debian, CentOS, RHEL, Rocky Linux

---

**May Allah bless this installation and make it beneficial for healthcare services. Ameen.**

*For technical support and updates, visit our GitHub repository.*
EOF
    
    echo -e "${GREEN}✅ README created${NC}"
}

# Function to create package archive
create_package_archive() {
    echo -e "${YELLOW}📦 Creating installation package archive...${NC}"
    
    cd "$PROJECT_DIR"
    
    # Create compressed archive
    tar -czf "zain-hms-offline-installer.tar.gz" -C "$OFFLINE_DIR" .
    
    # Get package size
    PACKAGE_SIZE=$(du -h "zain-hms-offline-installer.tar.gz" | cut -f1)
    
    echo -e "${GREEN}✅ Package created: zain-hms-offline-installer.tar.gz ($PACKAGE_SIZE)${NC}"
}

# Main function
main() {
    echo -e "${BLUE}Creating offline installation package for ZAIN HMS...${NC}"
    echo ""
    
    create_structure
    copy_application_files
    export_docker_images
    download_packages
    create_offline_installer
    create_readme
    create_package_archive
    
    echo ""
    echo -e "${GREEN}🎉 Offline installation package created successfully! 🎉${NC}"
    echo ""
    echo -e "${CYAN}Package Details:${NC}"
    echo "• Location: $PROJECT_DIR/zain-hms-offline-installer.tar.gz"
    echo "• Contents: Complete ZAIN HMS installation with all dependencies"
    echo "• Usage: Extract and run './install-offline.sh' on target server"
    echo ""
    echo -e "${YELLOW}To distribute this package:${NC}"
    echo "1. Upload to your server or share with others"
    echo "2. Extract: tar -xzf zain-hms-offline-installer.tar.gz"
    echo "3. Install: sudo ./install-offline.sh"
    echo ""
    echo -e "${GREEN}✨ May Allah bless this package and make it beneficial! ✨${NC}"
}

# Check if Docker is available
if ! command -v docker >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker is required to create the offline package${NC}"
    echo "Please install Docker and try again"
    exit 1
fi

# Run main function
main "$@"