#!/bin/bash
# 🏥 ZAIN HMS - One-Command Installation Script
# Download and install ZAIN HMS directly from GitHub
# Usage: curl -sSL https://raw.githubusercontent.com/Zain-Technologies-22/ZAIN-HMS/main/install.sh | bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
ZAIN_HMS_VERSION="latest"
GITHUB_REPO="ZainTechnologiesLTD/ZAIN-HMS"
INSTALL_DIR="/opt/zain-hms"
SERVICE_USER="zain-hms"
DOMAIN=""
SKIP_DOCKER_INSTALL=false
SKIP_SERVER_SETUP=false
INTERACTIVE_MODE=true

# Show banner
show_banner() {
    clear
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                              ║"
    echo "║    🏥 ZAIN HMS - Hospital Management System Installer                       ║"
    echo "║                                                                              ║"
    echo "║    Bismillahir Rahmanir Raheem                                              ║"
    echo "║    Version: ${ZAIN_HMS_VERSION}                                                          ║"
    echo "║    Repository: ${GITHUB_REPO}                                  ║"
    echo "║                                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
}

# Show usage
show_usage() {
    echo -e "${BLUE}Usage:${NC}"
    echo "  curl -sSL https://raw.githubusercontent.com/${GITHUB_REPO}/main/install.sh | bash"
    echo ""
    echo -e "${BLUE}Options:${NC}"
    echo "  -v, --version VERSION     Install specific version (default: latest)"
    echo "  -d, --domain DOMAIN       Set domain name for the installation"
    echo "  -i, --install-dir DIR     Installation directory (default: /opt/zain-hms)"
    echo "  --skip-docker            Skip Docker installation"
    echo "  --skip-setup             Skip server setup"
    echo "  --non-interactive        Run in non-interactive mode"
    echo "  -h, --help               Show this help message"
    echo ""
    echo -e "${BLUE}Examples:${NC}"
    echo "  # Basic installation"
    echo "  curl -sSL https://raw.githubusercontent.com/${GITHUB_REPO}/main/install.sh | bash"
    echo ""
    echo "  # Install with domain"
    echo "  curl -sSL https://raw.githubusercontent.com/${GITHUB_REPO}/main/install.sh | bash -s -- -d yourdomain.com"
    echo ""
    echo "  # Install specific version"
    echo "  curl -sSL https://raw.githubusercontent.com/${GITHUB_REPO}/main/install.sh | bash -s -- -v v2.1.0"
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -v|--version)
                ZAIN_HMS_VERSION="$2"
                shift 2
                ;;
            -d|--domain)
                DOMAIN="$2"
                shift 2
                ;;
            -i|--install-dir)
                INSTALL_DIR="$2"
                shift 2
                ;;
            --skip-docker)
                SKIP_DOCKER_INSTALL=true
                shift
                ;;
            --skip-setup)
                SKIP_SERVER_SETUP=true
                shift
                ;;
            --non-interactive)
                INTERACTIVE_MODE=false
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                echo -e "${RED}❌ Unknown option: $1${NC}"
                show_usage
                exit 1
                ;;
        esac
    done
}

# Check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}❌ This script must be run as root. Please use sudo.${NC}"
        echo "Example: curl -sSL https://raw.githubusercontent.com/${GITHUB_REPO}/main/install.sh | sudo bash"
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
    
    # Check if supported
    case "$OS" in
        *Ubuntu*|*Debian*)
            PACKAGE_MANAGER="apt"
            ;;
        *CentOS*|*Red\ Hat*|*Rocky*|*AlmaLinux*)
            PACKAGE_MANAGER="yum"
            ;;
        *)
            echo -e "${YELLOW}⚠️  OS not officially supported, but will try Ubuntu/Debian commands${NC}"
            PACKAGE_MANAGER="apt"
            ;;
    esac
}

# Interactive configuration
interactive_config() {
    if [ "$INTERACTIVE_MODE" = false ]; then
        return
    fi
    
    echo -e "${CYAN}🔧 Interactive Configuration${NC}"
    echo "================================="
    
    # Domain configuration
    if [ -z "$DOMAIN" ]; then
        echo ""
        echo -e "${BLUE}Enter your domain name (or press Enter for localhost):${NC}"
        read -p "Domain: " user_domain
        DOMAIN=${user_domain:-localhost}
    fi
    
    # Installation directory
    echo ""
    echo -e "${BLUE}Installation directory [${INSTALL_DIR}]:${NC}"
    read -p "Directory: " user_dir
    if [ -n "$user_dir" ]; then
        INSTALL_DIR="$user_dir"
    fi
    
    # Docker installation
    if ! command -v docker &> /dev/null; then
        echo ""
        echo -e "${BLUE}Docker is not installed. Install Docker? [Y/n]:${NC}"
        read -p "Install Docker: " install_docker
        if [[ "$install_docker" =~ ^[Nn]$ ]]; then
            SKIP_DOCKER_INSTALL=true
        fi
    fi
    
    echo ""
    echo -e "${GREEN}Configuration Summary:${NC}"
    echo "• Domain: $DOMAIN"
    echo "• Installation Directory: $INSTALL_DIR"
    echo "• Version: $ZAIN_HMS_VERSION"
    echo "• Skip Docker Install: $SKIP_DOCKER_INSTALL"
    echo ""
    echo -e "${BLUE}Continue with installation? [Y/n]:${NC}"
    read -p "Continue: " confirm
    if [[ "$confirm" =~ ^[Nn]$ ]]; then
        echo -e "${YELLOW}Installation cancelled${NC}"
        exit 0
    fi
}

# Install system dependencies
install_dependencies() {
    echo -e "${YELLOW}📦 Installing system dependencies...${NC}"
    
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
    
    echo -e "${GREEN}✅ System dependencies installed${NC}"
}

# Install Docker
install_docker() {
    if [ "$SKIP_DOCKER_INSTALL" = true ]; then
        echo -e "${YELLOW}⚠️  Skipping Docker installation${NC}"
        return
    fi
    
    if command -v docker &> /dev/null; then
        echo -e "${GREEN}✅ Docker already installed${NC}"
        return
    fi
    
    echo -e "${YELLOW}🐳 Installing Docker...${NC}"
    
    case "$PACKAGE_MANAGER" in
        apt)
            # Remove old versions
            apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
            
            # Install prerequisites
            apt install -y apt-transport-https ca-certificates curl gnupg lsb-release
            
            # Add Docker GPG key
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
            
            # Add Docker repository
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
            
            # Install Docker
            apt update
            apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            ;;
        yum)
            # Install Docker using convenience script
            curl -fsSL https://get.docker.com -o get-docker.sh
            sh get-docker.sh
            rm get-docker.sh
            ;;
    esac
    
    # Start and enable Docker
    systemctl start docker
    systemctl enable docker
    
    echo -e "${GREEN}✅ Docker installed and started${NC}"
}

# Install Docker Compose
install_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        echo -e "${GREEN}✅ Docker Compose already installed${NC}"
        return
    fi
    
    echo -e "${YELLOW}🔧 Installing Docker Compose...${NC}"
    
    # Get latest version
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | jq -r .tag_name)
    
    # Download and install
    curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    # Create symlink
    ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    
    echo -e "${GREEN}✅ Docker Compose installed${NC}"
}

# Create application user
create_app_user() {
    echo -e "${YELLOW}👤 Creating application user...${NC}"
    
    if id "$SERVICE_USER" &>/dev/null; then
        echo -e "${GREEN}✅ User $SERVICE_USER already exists${NC}"
    else
        useradd -m -s /bin/bash "$SERVICE_USER"
        usermod -aG docker "$SERVICE_USER"
        echo -e "${GREEN}✅ User $SERVICE_USER created${NC}"
    fi
}

# Download and extract ZAIN HMS
download_zain_hms() {
    echo -e "${YELLOW}📥 Downloading ZAIN HMS...${NC}"
    
    # Create installation directory
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    
    # Get download URL
    if [ "$ZAIN_HMS_VERSION" = "latest" ]; then
        DOWNLOAD_URL="https://api.github.com/repos/${GITHUB_REPO}/releases/latest"
        RELEASE_INFO=$(curl -s "$DOWNLOAD_URL")
        DOWNLOAD_URL=$(echo "$RELEASE_INFO" | jq -r '.tarball_url')
        ZAIN_HMS_VERSION=$(echo "$RELEASE_INFO" | jq -r '.tag_name')
    else
        DOWNLOAD_URL="https://github.com/${GITHUB_REPO}/archive/refs/tags/${ZAIN_HMS_VERSION}.tar.gz"
    fi
    
    echo -e "${BLUE}Downloading version: $ZAIN_HMS_VERSION${NC}"
    
    # Download and extract
    curl -L "$DOWNLOAD_URL" -o zain-hms.tar.gz
    tar -xzf zain-hms.tar.gz --strip-components=1
    rm zain-hms.tar.gz
    
    # Set ownership
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    
    echo -e "${GREEN}✅ ZAIN HMS downloaded and extracted${NC}"
}

# Setup directory structure
setup_directories() {
    echo -e "${YELLOW}📁 Setting up directory structure...${NC}"
    
    # Create data directories
    mkdir -p "$INSTALL_DIR/data"/{postgres,redis,static,media}
    mkdir -p "$INSTALL_DIR"/{logs,backups,ssl}
    
    # Set permissions
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    chmod -R 755 "$INSTALL_DIR"
    chmod -R 700 "$INSTALL_DIR/ssl"
    
    echo -e "${GREEN}✅ Directory structure created${NC}"
}

# Configure environment
configure_environment() {
    echo -e "${YELLOW}🔧 Configuring environment...${NC}"
    
    # Copy environment template
    cp "$INSTALL_DIR/.env.production.template" "$INSTALL_DIR/.env.prod"
    
    # Generate secure passwords
    DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    REDIS_PASSWORD=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-20)
    SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" 2>/dev/null || openssl rand -base64 75 | tr -d "=+/" | cut -c1-50)
    
    # Update environment file
    sed -i "s/your-very-secure-database-password-123/$DB_PASSWORD/g" "$INSTALL_DIR/.env.prod"
    sed -i "s/your-secure-redis-password-123/$REDIS_PASSWORD/g" "$INSTALL_DIR/.env.prod"
    sed -i "s/your-super-secret-django-key-here-must-be-50-characters-long-and-unique-123456789/$SECRET_KEY/g" "$INSTALL_DIR/.env.prod"
    sed -i "s/yourdomain.com/$DOMAIN/g" "$INSTALL_DIR/.env.prod"
    
    # Set secure permissions
    chmod 600 "$INSTALL_DIR/.env.prod"
    chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/.env.prod"
    
    echo -e "${GREEN}✅ Environment configured${NC}"
}

# Install system service
install_systemd_service() {
    echo -e "${YELLOW}⚙️  Installing systemd service...${NC}"
    
    cat > /etc/systemd/system/zain-hms.service << EOF
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
EOF
    
    # Reload systemd and enable service
    systemctl daemon-reload
    systemctl enable zain-hms
    
    echo -e "${GREEN}✅ Systemd service installed${NC}"
}

# Setup firewall
setup_firewall() {
    echo -e "${YELLOW}🔥 Configuring firewall...${NC}"
    
    if command -v ufw &> /dev/null; then
        # Configure UFW
        ufw --force reset
        ufw default deny incoming
        ufw default allow outgoing
        ufw allow ssh
        ufw allow 80/tcp
        ufw allow 443/tcp
        ufw --force enable
        echo -e "${GREEN}✅ UFW firewall configured${NC}"
    elif command -v firewall-cmd &> /dev/null; then
        # Configure firewalld
        systemctl enable firewalld
        systemctl start firewalld
        firewall-cmd --permanent --add-service=ssh
        firewall-cmd --permanent --add-service=http
        firewall-cmd --permanent --add-service=https
        firewall-cmd --reload
        echo -e "${GREEN}✅ Firewalld configured${NC}"
    else
        echo -e "${YELLOW}⚠️  No firewall manager found, please configure manually${NC}"
    fi
}

# Deploy application
deploy_application() {
    echo -e "${YELLOW}🚀 Deploying ZAIN HMS...${NC}"
    
    cd "$INSTALL_DIR"
    
    # Make scripts executable
    chmod +x scripts/*.sh
    chmod +x docker/entrypoint.prod.sh
    
    # Pull images
    sudo -u "$SERVICE_USER" docker-compose -f docker-compose.prod.yml pull
    
    # Start services
    sudo -u "$SERVICE_USER" docker-compose -f docker-compose.prod.yml up -d
    
    echo -e "${GREEN}✅ ZAIN HMS deployed${NC}"
}

# Wait for services
wait_for_services() {
    echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
    
    # Wait up to 2 minutes for services
    for i in {1..24}; do
        if curl -f http://localhost/health/ >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Services are ready!${NC}"
            return 0
        fi
        echo -e "${BLUE}Waiting... ($i/24)${NC}"
        sleep 5
    done
    
    echo -e "${YELLOW}⚠️  Services taking longer than expected${NC}"
}

# Show completion message
show_completion() {
    echo ""
    echo -e "${GREEN}🎉 ZAIN HMS Installation Completed Successfully! 🎉${NC}"
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                           INSTALLATION SUMMARY                              ║${NC}"
    echo -e "${CYAN}╠══════════════════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${CYAN}║${NC} Version: $ZAIN_HMS_VERSION"
    echo -e "${CYAN}║${NC} Installation Directory: $INSTALL_DIR"
    echo -e "${CYAN}║${NC} Domain: $DOMAIN"
    echo -e "${CYAN}║${NC} Service User: $SERVICE_USER"
    echo -e "${CYAN}╠══════════════════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${CYAN}║                              ACCESS INFORMATION                             ║${NC}"
    echo -e "${CYAN}╠══════════════════════════════════════════════════════════════════════════════╣${NC}"
    
    # Get server IP
    SERVER_IP=$(curl -s https://ipinfo.io/ip 2>/dev/null || hostname -I | awk '{print $1}')
    
    if [ "$DOMAIN" != "localhost" ]; then
        echo -e "${CYAN}║${NC} 🌐 Web Application: http://$DOMAIN"
        echo -e "${CYAN}║${NC} 🌐 Admin Panel: http://$DOMAIN/admin/"
    fi
    
    echo -e "${CYAN}║${NC} 🖥️  IP Access: http://$SERVER_IP"
    echo -e "${CYAN}║${NC} 🖥️  Admin via IP: http://$SERVER_IP/admin/"
    echo -e "${CYAN}║${NC} 👤 Default Admin: admin / admin123"
    echo -e "${CYAN}╠══════════════════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${CYAN}║                              SYSTEM COMMANDS                                ║${NC}"
    echo -e "${CYAN}╠══════════════════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${CYAN}║${NC} Start Service:    sudo systemctl start zain-hms"
    echo -e "${CYAN}║${NC} Stop Service:     sudo systemctl stop zain-hms"
    echo -e "${CYAN}║${NC} Restart Service:  sudo systemctl restart zain-hms"
    echo -e "${CYAN}║${NC} Check Status:     sudo systemctl status zain-hms"
    echo -e "${CYAN}║${NC} View Logs:        sudo docker-compose -f $INSTALL_DIR/docker-compose.prod.yml logs -f"
    echo -e "${CYAN}║${NC} Update System:    $INSTALL_DIR/scripts/update.sh"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    if [ "$DOMAIN" != "localhost" ]; then
        echo -e "${YELLOW}📝 Next Steps:${NC}"
        echo "1. Point your domain DNS to this server IP: $SERVER_IP"
        echo "2. Run: sudo certbot --nginx -d $DOMAIN (for SSL certificate)"
        echo "3. Change default admin password after first login"
        echo ""
    fi
    
    echo -e "${GREEN}✨ May Allah bless this installation and make it beneficial for healthcare! ✨${NC}"
    echo -e "${BLUE}🔗 Documentation: https://github.com/${GITHUB_REPO}/tree/main/docs${NC}"
    echo ""
}

# Main installation function
main() {
    show_banner
    parse_args "$@"
    check_root
    detect_os
    interactive_config
    
    echo -e "${CYAN}🚀 Starting ZAIN HMS Installation...${NC}"
    echo ""
    
    install_dependencies
    install_docker
    install_docker_compose
    create_app_user
    download_zain_hms
    setup_directories
    configure_environment
    install_systemd_service
    setup_firewall
    deploy_application
    wait_for_services
    show_completion
}

# Error handling
set -e
trap 'echo -e "${RED}❌ Installation failed at line $LINENO${NC}"; exit 1' ERR

# Run main function
main "$@"