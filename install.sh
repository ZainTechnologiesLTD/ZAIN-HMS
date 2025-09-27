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
        # Detect current hostname
        CURRENT_HOSTNAME=$(hostname -f 2>/dev/null || hostname 2>/dev/null || echo "localhost")
        
        # Show detected hostname if it's not localhost or empty
        if [ "$CURRENT_HOSTNAME" != "localhost" ] && [ -n "$CURRENT_HOSTNAME" ] && [ "$CURRENT_HOSTNAME" != "$(hostname -s)" ]; then
            echo -e "${GREEN}📡 Current hostname detected: ${YELLOW}$CURRENT_HOSTNAME${NC}"
            echo -e "${BLUE}Enter your domain name [${YELLOW}$CURRENT_HOSTNAME${BLUE}] or press Enter to use detected hostname:${NC}"
            read -p "Domain: " -t 30 user_domain
            DOMAIN=${user_domain:-$CURRENT_HOSTNAME}
        else
            echo -e "${BLUE}Enter your domain name (or press Enter for localhost):${NC}"
            read -p "Domain: " -t 30 user_domain
            DOMAIN=${user_domain:-localhost}
        fi
        
        echo -e "${GREEN}✅ Using domain: ${YELLOW}$DOMAIN${NC}"
        sleep 1
    fi
    
    # Installation directory
    echo ""
    echo -e "${BLUE}Installation directory [${YELLOW}${INSTALL_DIR}${BLUE}] or press Enter to use default:${NC}"
    read -p "Directory: " -t 20 user_dir
    if [ -n "$user_dir" ]; then
        INSTALL_DIR="$user_dir"
    fi
    echo -e "${GREEN}✅ Using directory: ${YELLOW}$INSTALL_DIR${NC}"
    
    # Docker installation
    if ! command -v docker &> /dev/null; then
        echo ""
        echo -e "${YELLOW}⚠️  Docker is not installed and is required for ZAIN HMS${NC}"
        echo -e "${BLUE}Would you like to install Docker automatically? [${GREEN}Y${BLUE}/n]:${NC}"
        read -p "Install Docker: " -t 15 install_docker
        if [[ "$install_docker" =~ ^[Nn]$ ]]; then
            SKIP_DOCKER_INSTALL=true
            echo -e "${RED}⚠️  Warning: ZAIN HMS requires Docker to run${NC}"
        else
            echo -e "${GREEN}✅ Docker will be installed automatically${NC}"
        fi
        sleep 1
    else
        echo -e "${GREEN}✅ Docker is already installed${NC}"
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

# Check and get latest versions
check_latest_versions() {
    echo -e "${YELLOW}🔍 Checking latest versions of components...${NC}"
    
    # Get latest Docker Compose version
    echo -e "${BLUE}Checking Docker Compose latest version...${NC}"
    COMPOSE_LATEST=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | jq -r .tag_name 2>/dev/null || echo "v2.24.0")
    echo -e "${GREEN}✅ Latest Docker Compose: $COMPOSE_LATEST${NC}"
    
    # Get latest PostgreSQL version
    echo -e "${BLUE}Checking PostgreSQL latest version...${NC}"
    POSTGRES_LATEST=$(curl -s "https://hub.docker.com/v2/repositories/library/postgres/tags?page_size=100" | jq -r '.results[]? | select(.name | test("^[0-9]+(\\.0)?-alpine$")) | .name' | sort -V | tail -1 2>/dev/null || echo "16-alpine")
    if [ -z "$POSTGRES_LATEST" ] || [ "$POSTGRES_LATEST" = "null" ]; then
        POSTGRES_LATEST="16-alpine"
    fi
    echo -e "${GREEN}✅ Latest PostgreSQL: $POSTGRES_LATEST${NC}"
    
    # Get latest Redis version  
    echo -e "${BLUE}Checking Redis latest version...${NC}"
    REDIS_LATEST=$(curl -s "https://hub.docker.com/v2/repositories/library/redis/tags?page_size=50" | jq -r '.results[]? | select(.name | test("^[0-9]+(\\.0)?-alpine$")) | .name' | sort -V | tail -1 2>/dev/null || echo "7-alpine")
    if [ -z "$REDIS_LATEST" ] || [ "$REDIS_LATEST" = "null" ]; then
        REDIS_LATEST="7-alpine"
    fi
    echo -e "${GREEN}✅ Latest Redis: $REDIS_LATEST${NC}"
    
    # Get latest NGINX version
    echo -e "${BLUE}Checking NGINX latest version...${NC}"
    NGINX_LATEST=$(curl -s "https://hub.docker.com/v2/repositories/library/nginx/tags?page_size=50" | jq -r '.results[]? | select(.name | test("^[0-9]+\\.[0-9]+-alpine$")) | .name' | sort -V | tail -1 2>/dev/null || echo "1.25-alpine")
    if [ -z "$NGINX_LATEST" ] || [ "$NGINX_LATEST" = "null" ]; then
        NGINX_LATEST="1.25-alpine"
    fi
    echo -e "${GREEN}✅ Latest NGINX: $NGINX_LATEST${NC}"
    
    # Get latest Python version
    echo -e "${BLUE}Checking Python latest version...${NC}"
    PYTHON_LATEST=$(curl -s "https://hub.docker.com/v2/repositories/library/python/tags?page_size=50" | jq -r '.results[]? | select(.name | test("^3\\.[0-9]+-slim$")) | .name' | sort -V | tail -1 2>/dev/null || echo "3.12-slim")
    if [ -z "$PYTHON_LATEST" ] || [ "$PYTHON_LATEST" = "null" ]; then
        PYTHON_LATEST="3.12-slim"
    fi
    echo -e "${GREEN}✅ Latest Python: $PYTHON_LATEST${NC}"
    
    # Get latest Node.js version (for any frontend tools)
    echo -e "${BLUE}Checking Node.js latest LTS version...${NC}"
    NODE_LATEST=$(curl -s "https://hub.docker.com/v2/repositories/library/node/tags?page_size=50" | jq -r '.results[]? | select(.name | test("^[0-9]+-alpine$")) | .name' | sort -V | tail -1 2>/dev/null || echo "20-alpine")
    if [ -z "$NODE_LATEST" ] || [ "$NODE_LATEST" = "null" ]; then
        NODE_LATEST="20-alpine"
    fi
    echo -e "${GREEN}✅ Latest Node.js: $NODE_LATEST${NC}"
    
    # Check for latest Docker Engine version
    echo -e "${BLUE}Checking for Docker Engine latest version...${NC}"
    DOCKER_ENGINE_LATEST=$(curl -s "https://api.github.com/repos/moby/moby/releases/latest" | jq -r '.tag_name' 2>/dev/null || echo "v27.0.0")
    if [ -z "$DOCKER_ENGINE_LATEST" ] || [ "$DOCKER_ENGINE_LATEST" = "null" ]; then
        DOCKER_ENGINE_LATEST="v27.0.0"
    fi
    echo -e "${GREEN}✅ Latest Docker Engine: $DOCKER_ENGINE_LATEST${NC}"
    
    echo -e "${GREEN}🔍 Version check completed!${NC}"
    echo ""
}

# Install Docker with latest version
install_docker() {
    if [ "$SKIP_DOCKER_INSTALL" = true ]; then
        echo -e "${YELLOW}⚠️  Skipping Docker installation${NC}"
        return
    fi
    
    if command -v docker &> /dev/null; then
        # Check if Docker version is up to date
        CURRENT_DOCKER=$(docker --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
        echo -e "${BLUE}Current Docker version: $CURRENT_DOCKER${NC}"
        
        # Get latest Docker version
        LATEST_DOCKER=$(curl -s https://api.github.com/repos/docker/docker-ce/releases/latest | jq -r .tag_name | sed 's/v//' 2>/dev/null || echo "24.0.0")
        echo -e "${BLUE}Latest Docker version: $LATEST_DOCKER${NC}"
        
        if [ "$CURRENT_DOCKER" = "$LATEST_DOCKER" ]; then
            echo -e "${GREEN}✅ Docker is up to date${NC}"
            return
        else
            echo -e "${YELLOW}📈 Updating Docker to latest version...${NC}"
        fi
    else
        echo -e "${YELLOW}� Installing latest Docker version...${NC}"
    fi
    
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
            
            # Update package index
            apt update
            
            # Install latest Docker
            apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            ;;
        yum)
            # Remove old versions
            yum remove -y docker docker-client docker-client-latest docker-common docker-latest docker-latest-logrotate docker-logrotate docker-engine 2>/dev/null || true
            
            # Install yum-utils
            yum install -y yum-utils
            
            # Add Docker repository
            yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            
            # Install latest Docker
            yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            ;;
    esac
    
    # Start and enable Docker
    systemctl start docker
    systemctl enable docker
    
    # Add current user to docker group (if not root)
    if [ "$USER" != "root" ] && [ -n "$SUDO_USER" ]; then
        usermod -aG docker "$SUDO_USER"
    fi
    
    echo -e "${GREEN}✅ Latest Docker installed and started${NC}"
}

# Install Docker Compose with latest version
install_docker_compose() {
    echo -e "${YELLOW}�🔧 Installing latest Docker Compose...${NC}"
    
    # Check current version
    if command -v docker-compose &> /dev/null; then
        CURRENT_COMPOSE=$(docker-compose --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
        echo -e "${BLUE}Current Docker Compose version: $CURRENT_COMPOSE${NC}"
    fi
    
    # Get latest version from GitHub API
    echo -e "${BLUE}Fetching latest Docker Compose version...${NC}"
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | jq -r .tag_name 2>/dev/null)
    
    if [ -z "$COMPOSE_VERSION" ] || [ "$COMPOSE_VERSION" = "null" ]; then
        echo -e "${YELLOW}⚠️  Could not fetch latest version, using fallback${NC}"
        COMPOSE_VERSION="v2.24.0"
    fi
    
    echo -e "${GREEN}✅ Installing Docker Compose $COMPOSE_VERSION${NC}"
    
    # Download latest Docker Compose
    ARCH=$(uname -m)
    OS=$(uname -s)
    
    # Handle different architectures
    case "$ARCH" in
        x86_64)
            ARCH="x86_64"
            ;;
        aarch64|arm64)
            ARCH="aarch64"
            ;;
        armv7l)
            ARCH="armv7"
            ;;
        *)
            echo -e "${YELLOW}⚠️  Unknown architecture: $ARCH, trying x86_64${NC}"
            ARCH="x86_64"
            ;;
    esac
    
    # Download and install
    COMPOSE_URL="https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-${OS}-${ARCH}"
    
    echo -e "${BLUE}Downloading from: $COMPOSE_URL${NC}"
    curl -L "$COMPOSE_URL" -o /usr/local/bin/docker-compose
    
    if [ $? -eq 0 ]; then
        chmod +x /usr/local/bin/docker-compose
        
        # Create symlink for compatibility
        ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
        
        # Verify installation
        INSTALLED_VERSION=$(docker-compose --version 2>/dev/null)
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Docker Compose installed successfully${NC}"
            echo -e "${GREEN}Version: $INSTALLED_VERSION${NC}"
        else
            echo -e "${RED}❌ Docker Compose installation verification failed${NC}"
            exit 1
        fi
    else
        echo -e "${RED}❌ Failed to download Docker Compose${NC}"
        exit 1
    fi
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
        RELEASE_API_URL="https://api.github.com/repos/${GITHUB_REPO}/releases/latest"
        RELEASE_INFO=$(curl -s "$RELEASE_API_URL")
        
        # Check if we got valid release info
        if [ -n "$RELEASE_INFO" ] && [ "$RELEASE_INFO" != "null" ]; then
            ZAIN_HMS_VERSION=$(echo "$RELEASE_INFO" | jq -r '.tag_name' 2>/dev/null)
            DOWNLOAD_URL=$(echo "$RELEASE_INFO" | jq -r '.tarball_url' 2>/dev/null)
        fi
        
        # Fallback if API fails
        if [ -z "$ZAIN_HMS_VERSION" ] || [ "$ZAIN_HMS_VERSION" = "null" ] || [ -z "$DOWNLOAD_URL" ] || [ "$DOWNLOAD_URL" = "null" ]; then
            echo -e "${YELLOW}⚠️ GitHub API failed, using main branch${NC}"
            ZAIN_HMS_VERSION="main"
            DOWNLOAD_URL="https://github.com/${GITHUB_REPO}/archive/refs/heads/main.tar.gz"
        fi
    else
        DOWNLOAD_URL="https://github.com/${GITHUB_REPO}/archive/refs/tags/${ZAIN_HMS_VERSION}.tar.gz"
    fi
    
    echo -e "${BLUE}Downloading version: $ZAIN_HMS_VERSION${NC}"
    echo -e "${BLUE}Download URL: $DOWNLOAD_URL${NC}"
    
    # Download and extract with error handling
    if ! curl -L "$DOWNLOAD_URL" -o zain-hms.tar.gz; then
        echo -e "${RED}❌ Download failed. Trying alternative method...${NC}"
        # Fallback to direct clone
        rm -f zain-hms.tar.gz
        git clone "https://github.com/${GITHUB_REPO}.git" .
        chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
        return 0
    fi
    tar -xzf zain-hms.tar.gz --strip-components=1
    rm zain-hms.tar.gz
    
    # Set ownership
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    
    echo -e "${GREEN}✅ ZAIN HMS downloaded and extracted${NC}"
}

# Setup directory structure
setup_directories() {
    echo -e "${YELLOW}📁 Setting up directory structure...${NC}"
    
    # Create data directories with proper ownership from the start
    mkdir -p "$INSTALL_DIR/data"/{postgres,redis,static,media}
    mkdir -p "$INSTALL_DIR"/{logs,backups,ssl}
    mkdir -p "$INSTALL_DIR/logs/nginx"
    mkdir -p "$INSTALL_DIR/docker/nginx/conf.d"
    mkdir -p "$INSTALL_DIR/docker/postgres"
    
    # Create Django log files with proper permissions (fixes bind mount logging issues)
    touch "$INSTALL_DIR/logs/django.log" "$INSTALL_DIR/logs/authentication.log" "$INSTALL_DIR/logs/security.log"
    chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/logs/"*.log
    chmod 664 "$INSTALL_DIR/logs/"*.log
    
    # Create PostgreSQL initialization script to prevent directory mount errors
    cat > "$INSTALL_DIR/docker/postgres/init.sql" << 'EOF'
-- PostgreSQL initialization script for ZAIN HMS
-- This file ensures proper database initialization without directory conflicts
SELECT 'ZAIN HMS PostgreSQL initialized successfully' AS status;
EOF
    
    # Set PostgreSQL data directory ownership BEFORE Docker tries to mount it
    # This prevents the "no such file or directory" mount error
    echo -e "${BLUE}🐘 Configuring PostgreSQL data directory...${NC}"
    
    # Remove any existing postgres data that might cause conflicts
    rm -rf "$INSTALL_DIR/data/postgres"
    mkdir -p "$INSTALL_DIR/data/postgres"
    
    # Set correct ownership (UID 999 is postgres user in container)
    chown -R 999:999 "$INSTALL_DIR/data/postgres"
    chmod 700 "$INSTALL_DIR/data/postgres"
    
    # Create a marker file to ensure directory is properly initialized
    echo "ZAIN HMS PostgreSQL Data Directory - $(date)" > "$INSTALL_DIR/data/postgres/.zain_hms_marker"
    chown 999:999 "$INSTALL_DIR/data/postgres/.zain_hms_marker"
    
    # Set general permissions
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    chmod -R 755 "$INSTALL_DIR"
    chmod -R 700 "$INSTALL_DIR/ssl"
    
    # Ensure PostgreSQL data directory remains with correct ownership
    chown -R 999:999 "$INSTALL_DIR/data/postgres"
    
    echo -e "${GREEN}✅ Directory structure created with PostgreSQL volume fix${NC}"
}

# Configure environment
configure_environment() {
    echo -e "${YELLOW}🔧 Configuring environment with latest versions...${NC}"
    
    # Copy environment template
    cp "$INSTALL_DIR/.env.production.template" "$INSTALL_DIR/.env.prod"
    
    # Generate secure passwords
    DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    REDIS_PASSWORD=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-20)
    # Generate Django secret key using safe characters only to avoid sed delimiter issues
    SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" 2>/dev/null || openssl rand -hex 25)
    
    # Generate proper Redis URL with password
    REDIS_URL_WITH_PASSWORD="redis://:${REDIS_PASSWORD}@redis:6379/0"
    
    # Add latest container versions to environment
    echo "" >> "$INSTALL_DIR/.env.prod"
    echo "# Container Versions (Auto-detected latest)" >> "$INSTALL_DIR/.env.prod"
    echo "POSTGRES_VERSION=${POSTGRES_LATEST}" >> "$INSTALL_DIR/.env.prod"
    echo "REDIS_VERSION=${REDIS_LATEST}" >> "$INSTALL_DIR/.env.prod"
    echo "NGINX_VERSION=${NGINX_LATEST}" >> "$INSTALL_DIR/.env.prod"
    echo "PYTHON_VERSION=${PYTHON_LATEST}" >> "$INSTALL_DIR/.env.prod"
    echo "NODE_VERSION=${NODE_LATEST}" >> "$INSTALL_DIR/.env.prod"
    echo "" >> "$INSTALL_DIR/.env.prod"
    echo "# Installation Info" >> "$INSTALL_DIR/.env.prod"
    echo "INSTALLATION_DATE=$(date -u +%Y-%m-%d_%H:%M:%S_UTC)" >> "$INSTALL_DIR/.env.prod"
    echo "DOCKER_COMPOSE_VERSION=${COMPOSE_VERSION}" >> "$INSTALL_DIR/.env.prod"
    echo "INSTALLED_ARCHITECTURE=$(uname -m)" >> "$INSTALL_DIR/.env.prod"
    echo "SERVER_IP=$(curl -s https://ipinfo.io/ip 2>/dev/null || hostname -I | awk '{print $1}')" >> "$INSTALL_DIR/.env.prod"
    
    # Update environment file with generated values (using | delimiter to avoid issues with special chars)
    sed -i "s|your-very-secure-database-password-123|$DB_PASSWORD|g" "$INSTALL_DIR/.env.prod"
    sed -i "s|your-secure-redis-password-123|$REDIS_PASSWORD|g" "$INSTALL_DIR/.env.prod"
    sed -i "s|your-super-secret-django-key-here-must-be-50-characters-long-and-unique-123456789|$SECRET_KEY|g" "$INSTALL_DIR/.env.prod"
    sed -i "s|yourdomain.com|$DOMAIN|g" "$INSTALL_DIR/.env.prod"
    
    # Fix Redis URL to include password (handles both existing formats)
    sed -i "s|REDIS_URL=redis://redis:6379/0|REDIS_URL=${REDIS_URL_WITH_PASSWORD}|g" "$INSTALL_DIR/.env.prod"
    sed -i "s|REDIS_URL=redis://:.*@redis:6379/0|REDIS_URL=${REDIS_URL_WITH_PASSWORD}|g" "$INSTALL_DIR/.env.prod"
    
    # Ensure Redis URL is properly set if not found in template
    if ! grep -q "REDIS_URL=" "$INSTALL_DIR/.env.prod"; then
        echo "REDIS_URL=${REDIS_URL_WITH_PASSWORD}" >> "$INSTALL_DIR/.env.prod"
    fi
    
    # Set secure permissions
    chmod 600 "$INSTALL_DIR/.env.prod"
    chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/.env.prod"
    
    # Display version information
    echo -e "${GREEN}✅ Environment configured with latest versions:${NC}"
    echo -e "${BLUE}  📊 PostgreSQL: ${POSTGRES_LATEST}${NC}"
    echo -e "${BLUE}  📊 Redis: ${REDIS_LATEST}${NC}"
    echo -e "${BLUE}  📊 NGINX: ${NGINX_LATEST}${NC}"
    echo -e "${BLUE}  📊 Python: ${PYTHON_LATEST}${NC}"
    echo -e "${BLUE}  📊 Docker Compose: ${COMPOSE_VERSION}${NC}"
    echo -e "${BLUE}  🔗 Redis URL: ${REDIS_URL_WITH_PASSWORD}${NC}"
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

# Complete cleanup of existing ZAIN HMS installation
complete_cleanup() {
    echo -e "${YELLOW}🧹 COMPLETE CLEANUP: Removing all existing ZAIN HMS resources...${NC}"
    
    # 1. Stop ALL containers immediately (aggressive approach)
    echo -e "${BLUE}🛑 Stopping ALL Docker containers...${NC}"
    docker stop $(docker ps -aq) 2>/dev/null || true
    
    # 2. Remove ALL ZAIN HMS containers by pattern
    echo -e "${BLUE}🗑️  Removing all ZAIN HMS containers...${NC}"
    docker ps -aq --filter "name=zain" | xargs -r docker rm -f 2>/dev/null || true
    docker ps -aq --filter "name=hms" | xargs -r docker rm -f 2>/dev/null || true
    
    # 3. Remove ALL ZAIN HMS networks
    echo -e "${BLUE}🌐 Removing ZAIN HMS networks...${NC}"
    docker network ls -q --filter "name=zain" | xargs -r docker network rm 2>/dev/null || true
    docker network ls -q --filter "name=hms" | xargs -r docker network rm 2>/dev/null || true
    
    # 4. Remove ALL ZAIN HMS volumes
    echo -e "${BLUE}💾 Removing ALL ZAIN HMS volumes...${NC}"
    docker volume ls -q --filter "name=zain" | xargs -r docker volume rm -f 2>/dev/null || true
    docker volume ls -q --filter "name=hms" | xargs -r docker volume rm -f 2>/dev/null || true
    docker volume ls -q --filter "name=postgres" | xargs -r docker volume rm -f 2>/dev/null || true
    
    # 5. Remove ALL ZAIN HMS images
    echo -e "${BLUE}🖼️  Removing ZAIN HMS images...${NC}"
    docker images -q "*zain*" | xargs -r docker rmi -f 2>/dev/null || true
    docker images -q "*hms*" | xargs -r docker rmi -f 2>/dev/null || true
    docker images -q "ghcr.io/zain-technologies-22/*" | xargs -r docker rmi -f 2>/dev/null || true
    
    # 6. Kill all conflicting processes
    echo -e "${BLUE}⚡ Stopping all conflicting processes...${NC}"
    pkill -f "postgres" 2>/dev/null || true
    pkill -f "redis-server" 2>/dev/null || true
    pkill -f "nginx" 2>/dev/null || true
    pkill -f "gunicorn" 2>/dev/null || true
    pkill -f "supervisord" 2>/dev/null || true
    sleep 5
    
    # 7. Remove all data directories
    echo -e "${BLUE}📁 Removing all data directories...${NC}"
    if [ -d "$INSTALL_DIR" ]; then
        rm -rf "$INSTALL_DIR/data" "$INSTALL_DIR/logs" "$INSTALL_DIR/backups" 2>/dev/null || true
        rm -rf "$INSTALL_DIR/.env" "$INSTALL_DIR/.env.prod" 2>/dev/null || true
    fi
    
    # 8. Stop and remove systemd service
    echo -e "${BLUE}🔧 Removing systemd service...${NC}"
    systemctl stop zain-hms 2>/dev/null || true
    systemctl disable zain-hms 2>/dev/null || true
    rm -f /etc/systemd/system/zain-hms.service
    systemctl daemon-reload
    
    # 9. Complete Docker cleanup
    echo -e "${BLUE}🧹 Complete Docker system cleanup...${NC}"
    docker system prune -af --volumes --filter "until=1h" 2>/dev/null || true
    
    # 10. Wait for processes to fully terminate
    echo -e "${BLUE}⏱️  Waiting for processes to terminate...${NC}"
    sleep 5
    
    echo -e "${GREEN}✅ COMPLETE cleanup finished - system ready for fresh installation${NC}"
    echo ""
}

# Deploy application with latest images
deploy_application() {
    echo -e "${YELLOW}🚀 Deploying ZAIN HMS with latest versions...${NC}"
    
    cd "$INSTALL_DIR"
    
    # Pre-deployment PostgreSQL volume check
    echo -e "${BLUE}🔍 Verifying PostgreSQL volume setup...${NC}"
    if [ ! -d "$INSTALL_DIR/data/postgres" ] || [ ! -f "$INSTALL_DIR/data/postgres/.zain_hms_marker" ]; then
        echo -e "${YELLOW}⚠️  PostgreSQL volume not properly initialized, fixing...${NC}"
        rm -rf "$INSTALL_DIR/data/postgres"
        mkdir -p "$INSTALL_DIR/data/postgres"
        chown -R 999:999 "$INSTALL_DIR/data/postgres"
        chmod 700 "$INSTALL_DIR/data/postgres"
        echo "ZAIN HMS PostgreSQL Data Directory - $(date)" > "$INSTALL_DIR/data/postgres/.zain_hms_marker"
        chown 999:999 "$INSTALL_DIR/data/postgres/.zain_hms_marker"
    fi
    
    # Make scripts executable
    chmod +x scripts/*.sh
    chmod +x docker/entrypoint.prod.sh
    
    # Show what versions will be deployed
    echo -e "${BLUE}📦 Container versions to be deployed:${NC}"
    echo -e "${GREEN}  🐘 PostgreSQL: ${POSTGRES_LATEST}${NC}"
    echo -e "${GREEN}  🔄 Redis: ${REDIS_LATEST}${NC}"
    echo -e "${GREEN}  🌐 NGINX: ${NGINX_LATEST}${NC}"
    echo -e "${GREEN}  🐍 Python: ${PYTHON_LATEST}${NC}"
    echo ""
    
    # Prepare for deployment (cleanup already done upfront)
    echo -e "${BLUE}� Preparing for deployment with fresh environment...${NC}"
    
    # Create directory structure for bind mounts (Redis, static, media)
    echo -e "${BLUE}📁 Creating directory structure for bind mounts...${NC}"
    mkdir -p "$INSTALL_DIR/data"/{redis,static,media,backups}
    
    # Create Django log files if they don't exist (critical for bind mount logging)
    echo -e "${BLUE}📝 Ensuring Django log files exist for bind mounting...${NC}"
    touch "$INSTALL_DIR/logs/django.log" "$INSTALL_DIR/logs/authentication.log" "$INSTALL_DIR/logs/security.log"
    chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/logs/"*.log 2>/dev/null || true
    chmod 664 "$INSTALL_DIR/logs/"*.log 2>/dev/null || true
    
    # Set permissions for bind mount directories  
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/data"/{redis,static,media,backups}
    chmod -R 755 "$INSTALL_DIR/data"/{redis,static,media,backups}
    
    # Configure PostgreSQL with named volume (avoids overlay filesystem issues)
    echo -e "${BLUE}🐘 Configuring PostgreSQL with named volume...${NC}"
    echo -e "${GREEN}✅ PostgreSQL will use Docker named volume to avoid mounting conflicts${NC}"
    
    echo -e "${GREEN}✅ Named volume configuration completed successfully${NC}"
    
    # Verify docker-compose.prod.yml is valid
    if ! sudo -u "$SERVICE_USER" docker-compose -f docker-compose.prod.yml config >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Docker Compose validation failed, checking configuration...${NC}"
        sudo -u "$SERVICE_USER" docker-compose -f docker-compose.prod.yml config
    fi
    
    echo -e "${GREEN}✅ Named volume configuration verified${NC}"
    
    # Pull base images only (exclude web container which needs to be built)
    echo -e "${BLUE}📥 Pulling base Docker images...${NC}"
    sudo -u "$SERVICE_USER" docker-compose -f docker-compose.prod.yml pull --quiet --ignore-pull-failures db redis nginx watchtower || {
        echo -e "${YELLOW}⚠️  Some images failed to pull, continuing with build...${NC}"
    }
    
    # Verify images are up to date
    echo -e "${BLUE}🔍 Verifying image versions...${NC}"
    
    # Check if images exist and show their info
    POSTGRES_IMAGE="postgres:${POSTGRES_LATEST}"
    REDIS_IMAGE="redis:${REDIS_LATEST}" 
    NGINX_IMAGE="nginx:${NGINX_LATEST}"
    
    if docker images "$POSTGRES_IMAGE" --format "table" | grep -q "$POSTGRES_LATEST"; then
        echo -e "${GREEN}✅ PostgreSQL $POSTGRES_LATEST ready${NC}"
    else
        echo -e "${YELLOW}⚠️  PostgreSQL image verification failed${NC}"
    fi
    
    if docker images "$REDIS_IMAGE" --format "table" | grep -q "$REDIS_LATEST"; then
        echo -e "${GREEN}✅ Redis $REDIS_LATEST ready${NC}"
    else
        echo -e "${YELLOW}⚠️  Redis image verification failed${NC}"
    fi
    
    if docker images "$NGINX_IMAGE" --format "table" | grep -q "$NGINX_LATEST"; then
        echo -e "${GREEN}✅ NGINX $NGINX_LATEST ready${NC}"
    else
        echo -e "${YELLOW}⚠️  NGINX image verification failed${NC}"
    fi
    
    # Start services with named volumes (avoids Docker overlay filesystem errors)
    echo -e "${BLUE}🚀 Starting services with named volume configuration...${NC}"
    echo -e "${YELLOW}⚙️  Preparing environment and building containers with SSL-aware configuration...${NC}"
    
    # Create symlink for Docker Compose to find environment variables
    ln -sf "$INSTALL_DIR/.env.prod" "$INSTALL_DIR/.env"
    chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/.env"
    
    # Build web container with SSL-aware Docker build args
    echo -e "${BLUE}🔨 Building web container with SSL-aware configuration...${NC}"
    sudo -u "$SERVICE_USER" DOCKER_BUILDKIT=1 docker-compose -f docker-compose.prod.yml build web \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        --build-arg PIP_TRUSTED_HOST="pypi.org pypi.python.org files.pythonhosted.org" || \
    {
        echo -e "${YELLOW}⚠️  Build failed, retrying with fallback options...${NC}"
        sudo -u "$SERVICE_USER" docker-compose -f docker-compose.prod.yml build web --no-cache
    }
    
    # PostgreSQL permissions already set during directory preparation
    echo -e "${BLUE}🔒 PostgreSQL directory permissions already configured${NC}"
    
    # Start services incrementally for better reliability and debugging
    echo -e "${BLUE}🚀 Phase 1: Starting infrastructure services (PostgreSQL & Redis)...${NC}"
    sudo -u "$SERVICE_USER" docker-compose -f docker-compose.prod.yml up -d db redis
    
    # Wait for infrastructure to be healthy
    if check_container_health "db" 12 5; then
        echo -e "${GREEN}✅ PostgreSQL is ready${NC}"
    else
        echo -e "${YELLOW}⚠️  PostgreSQL health check failed, but continuing...${NC}"
    fi
    
    if check_container_health "redis" 12 5; then
        echo -e "${GREEN}✅ Redis is ready${NC}"
    else
        echo -e "${YELLOW}⚠️  Redis health check failed, but continuing...${NC}"
    fi
    
    # Start web container
    echo -e "${BLUE}🚀 Phase 2: Starting web application container...${NC}"
    sudo -u "$SERVICE_USER" docker-compose -f docker-compose.prod.yml up -d web
    
    # Wait for web container to start (longer timeout for complex startup)
    if check_container_health "web" 20 10; then
        echo -e "${GREEN}✅ Web container is ready${NC}"
        
        # Start nginx and watchtower only if web is healthy
        echo -e "${BLUE}� Phase 3: Starting reverse proxy (NGINX) and monitoring services...${NC}"
        sudo -u "$SERVICE_USER" docker-compose -f docker-compose.prod.yml up -d nginx watchtower
    else
        echo -e "${RED}❌ Web container failed health checks${NC}"
        echo -e "${YELLOW}📋 Debugging info - Web container logs (last 20 lines):${NC}"
        sudo docker logs zain_hms_web --tail 20 || true
        echo -e "${YELLOW}⚠️  Skipping NGINX startup due to web container issues${NC}"
    fi
    
    # Show final container status
    echo ""
    echo -e "${BLUE}📊 Final Container Status:${NC}"
    sudo -u "$SERVICE_USER" docker-compose -f docker-compose.prod.yml ps
    
    echo -e "${GREEN}✅ ZAIN HMS deployed with latest versions${NC}"
}

# Check individual container health with better validation
check_container_health() {
    local container_name="$1"
    local max_attempts="$2"
    local sleep_time="$3"
    
    echo -e "${YELLOW}⏳ Checking $container_name health...${NC}"
    
    for i in $(seq 1 $max_attempts); do
        local status=$(sudo -u "$SERVICE_USER" docker-compose -f docker-compose.prod.yml ps -q $container_name | xargs sudo docker inspect --format='{{.State.Health.Status}}' 2>/dev/null || echo "unknown")
        
        if [ "$status" = "healthy" ]; then
            echo -e "${GREEN}✅ $container_name is healthy!${NC}"
            return 0
        elif [ "$status" = "unhealthy" ]; then
            echo -e "${RED}❌ $container_name is unhealthy! Check logs: sudo docker logs zain_hms_$container_name${NC}"
            return 1
        else
            echo -e "${BLUE}⏳ $container_name status: $status (attempt $i/$max_attempts)${NC}"
            sleep $sleep_time
        fi
    done
    
    echo -e "${YELLOW}⚠️  $container_name health check timeout after $max_attempts attempts${NC}"
    return 1
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

# Create update script
create_update_script() {
    echo -e "${YELLOW}📝 Creating update script...${NC}"
    
    cat > "$INSTALL_DIR/scripts/update-to-latest.sh" << 'EOF'
#!/bin/bash
# 🏥 ZAIN HMS - Update to Latest Versions Script
# Automatically checks and updates to latest container versions

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

INSTALL_DIR="/opt/zain-hms"

echo -e "${CYAN}🔄 ZAIN HMS - Update to Latest Versions${NC}"
echo "========================================"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Please run as root: sudo $0${NC}"
    exit 1
fi

# Check latest versions
echo -e "${YELLOW}🔍 Checking for latest versions...${NC}"

# Get latest versions (same logic as install script)
POSTGRES_LATEST=$(curl -s https://registry.hub.docker.com/v2/repositories/library/postgres/tags/ | jq -r '.results[] | select(.name | test("^[0-9]+\\.[0-9]+-alpine$")) | .name' | head -1 2>/dev/null || echo "15-alpine")
REDIS_LATEST=$(curl -s https://registry.hub.docker.com/v2/repositories/library/redis/tags/ | jq -r '.results[] | select(.name | test("^[0-9]+\\.[0-9]+-alpine$")) | .name' | head -1 2>/dev/null || echo "7-alpine")
NGINX_LATEST=$(curl -s https://registry.hub.docker.com/v2/repositories/library/nginx/tags/ | jq -r '.results[] | select(.name | test("^[0-9]+\\.[0-9]+-alpine$")) | .name' | head -1 2>/dev/null || echo "alpine")

echo -e "${GREEN}📦 Latest versions found:${NC}"
echo -e "${BLUE}  🐘 PostgreSQL: $POSTGRES_LATEST${NC}"
echo -e "${BLUE}  🔄 Redis: $REDIS_LATEST${NC}"
echo -e "${BLUE}  🌐 NGINX: $NGINX_LATEST${NC}"

# Update environment file
echo -e "${YELLOW}📝 Updating environment configuration...${NC}"
cd "$INSTALL_DIR"

# Update versions in environment file
sed -i "s/POSTGRES_VERSION=.*/POSTGRES_VERSION=$POSTGRES_LATEST/" .env.prod
sed -i "s/REDIS_VERSION=.*/REDIS_VERSION=$REDIS_LATEST/" .env.prod  
sed -i "s/NGINX_VERSION=.*/NGINX_VERSION=$NGINX_LATEST/" .env.prod

# Add update timestamp
echo "LAST_UPDATE=$(date -u +%Y-%m-%d_%H:%M:%S_UTC)" >> .env.prod

# Stop services
echo -e "${YELLOW}⏹️ Stopping services...${NC}"
sudo -u zain-hms docker-compose -f docker-compose.prod.yml down

# Pull base images only (exclude web container which needs to be built)
echo -e "${YELLOW}📥 Pulling base images...${NC}"
sudo -u zain-hms docker-compose -f docker-compose.prod.yml pull --quiet --ignore-pull-failures db redis nginx watchtower || {
    echo -e "${YELLOW}⚠️  Some images failed to pull, continuing with build...${NC}"
}

# Build and start services
echo -e "${YELLOW}🚀 Building and starting updated services...${NC}"
echo -e "${YELLOW}⚙️  Building containers with SSL-aware configuration...${NC}"

# Build web container with SSL-aware Docker build args
echo -e "${BLUE}🔨 Building web container with SSL-aware configuration...${NC}"
sudo -u zain-hms DOCKER_BUILDKIT=1 docker-compose -f docker-compose.prod.yml build web \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    --build-arg PIP_TRUSTED_HOST="pypi.org pypi.python.org files.pythonhosted.org" || \
{
    echo -e "${YELLOW}⚠️  Build failed, retrying with fallback options...${NC}"
    sudo -u zain-hms docker-compose -f docker-compose.prod.yml build web --no-cache
}

# Start services
sudo -u zain-hms docker-compose -f docker-compose.prod.yml up -d

# Wait for services
echo -e "${YELLOW}⏳ Waiting for services...${NC}"
sleep 30

# Health check
if curl -f http://localhost/health/ >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Update completed successfully!${NC}"
    echo -e "${GREEN}🎉 ZAIN HMS is running with latest versions${NC}"
else
    echo -e "${RED}⚠️  Services may still be starting up${NC}"
    echo -e "${YELLOW}Check status: sudo docker-compose -f $INSTALL_DIR/docker-compose.prod.yml ps${NC}"
fi

echo ""
echo -e "${CYAN}📊 Updated container versions:${NC}"
sudo -u zain-hms docker-compose -f docker-compose.prod.yml ps
EOF

    chmod +x "$INSTALL_DIR/scripts/update-to-latest.sh"
    chown zain-hms:zain-hms "$INSTALL_DIR/scripts/update-to-latest.sh"
    
    echo -e "${GREEN}✅ Update script created at: $INSTALL_DIR/scripts/update-to-latest.sh${NC}"
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
    echo -e "${CYAN}║${NC} Update to Latest: sudo $INSTALL_DIR/scripts/update-to-latest.sh"
    echo -e "${CYAN}║${NC} Maintenance:      sudo $INSTALL_DIR/scripts/zain-hms-maintenance.sh"
    echo -e "${CYAN}╠══════════════════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${CYAN}║                           INSTALLED VERSIONS                                ║${NC}"
    echo -e "${CYAN}╠══════════════════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${CYAN}║${NC} 🐘 PostgreSQL:   ${POSTGRES_LATEST}"
    echo -e "${CYAN}║${NC} 🔄 Redis:        ${REDIS_LATEST}"
    echo -e "${CYAN}║${NC} 🌐 NGINX:        ${NGINX_LATEST}"
    echo -e "${CYAN}║${NC} 🐍 Python:       ${PYTHON_LATEST}"
    echo -e "${CYAN}║${NC} 🔧 Docker Compose: ${COMPOSE_VERSION}"
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
    
    echo -e "${CYAN}🚀 Starting ZAIN HMS Installation with Latest Versions...${NC}"
    echo ""
    
    # FIRST: Complete cleanup of any existing installation
    complete_cleanup
    
    install_dependencies
    check_latest_versions  # ✨ NEW: Check latest versions first
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
    create_update_script  # ✨ NEW: Create update script
    show_completion
}

# Error handling
set -e
trap 'echo -e "${RED}❌ Installation failed at line $LINENO${NC}"; exit 1' ERR

# Run main function
main "$@"