#!/bin/bash
# 🚀 ZAIN HMS Automated Deployment Script
# Handles deployment from development to production server

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Default values
SERVER_IP=""
SERVER_USER="root"
DOMAIN="localhost"
ENVIRONMENT="production"
DEPLOY_KEY=""

# Function to show usage
show_usage() {
    echo -e "${BLUE}🏥 ZAIN HMS Automated Deployment Script${NC}"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -s, --server IP        Production server IP address (required)"
    echo "  -u, --user USER        SSH user for server connection (default: root)"
    echo "  -d, --domain DOMAIN    Domain name for the application (default: localhost)"
    echo "  -k, --key PATH         Path to SSH private key"
    echo "  -e, --env ENV          Environment (production/staging, default: production)"
    echo "  -h, --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -s 192.168.1.100 -d zainhms.com"
    echo "  $0 --server 10.0.0.50 --user ubuntu --domain example.com --key ~/.ssh/production_key"
}

# Function to parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -s|--server)
                SERVER_IP="$2"
                shift 2
                ;;
            -u|--user)
                SERVER_USER="$2"
                shift 2
                ;;
            -d|--domain)
                DOMAIN="$2"
                shift 2
                ;;
            -k|--key)
                DEPLOY_KEY="$2"
                shift 2
                ;;
            -e|--env)
                ENVIRONMENT="$2"
                shift 2
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

    # Validate required parameters
    if [ -z "$SERVER_IP" ]; then
        echo -e "${RED}❌ Server IP is required!${NC}"
        show_usage
        exit 1
    fi
}

# Function to validate prerequisites
validate_prerequisites() {
    echo -e "${YELLOW}🔍 Validating prerequisites...${NC}"

    # Check if we're in the correct directory
    if [ ! -f "$PROJECT_DIR/manage.py" ]; then
        echo -e "${RED}❌ Not in ZAIN HMS project directory!${NC}"
        exit 1
    fi

    # Check if Docker is available locally (for testing)
    if ! command -v docker &> /dev/null; then
        echo -e "${YELLOW}⚠️  Docker not found locally (needed for local testing)${NC}"
    fi

    # Check SSH connectivity
    echo -e "${YELLOW}🔗 Testing SSH connection to server...${NC}"
    
    SSH_CMD="ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no"
    if [ -n "$DEPLOY_KEY" ]; then
        SSH_CMD="$SSH_CMD -i $DEPLOY_KEY"
    fi

    if $SSH_CMD "$SERVER_USER@$SERVER_IP" "echo 'SSH connection successful'" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ SSH connection successful${NC}"
    else
        echo -e "${RED}❌ Cannot connect to server via SSH!${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ Prerequisites validated${NC}"
}

# Function to prepare deployment package
prepare_deployment() {
    echo -e "${YELLOW}📦 Preparing deployment package...${NC}"

    # Create temporary deployment directory
    DEPLOY_DIR="/tmp/zain_hms_deploy_$(date +%s)"
    mkdir -p "$DEPLOY_DIR"

    # Copy necessary files
    cp "$PROJECT_DIR/docker-compose.prod.yml" "$DEPLOY_DIR/"
    cp -r "$PROJECT_DIR/docker" "$DEPLOY_DIR/"
    cp -r "$PROJECT_DIR/scripts" "$DEPLOY_DIR/"

    # Create environment template
    cat > "$DEPLOY_DIR/.env.prod.template" << EOF
# 🏥 ZAIN HMS Production Environment Configuration
# Copy this to .env.prod and fill in the actual values

# Application Settings
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=your-super-secret-key-here-50-characters-long
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN,localhost,127.0.0.1
MAIN_DOMAIN=$DOMAIN

# Database Configuration
DB_NAME=zain_hms
DB_USER=zain_hms_user
DB_PASSWORD=your-secure-database-password
DB_HOST=db
DB_PORT=5432

# Redis Configuration
REDIS_PASSWORD=your-redis-password

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-email-password
EMAIL_USE_TLS=True

# AWS Configuration (for file storage)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_STORAGE_BUCKET_NAME=zain-hms-media
AWS_S3_REGION_NAME=us-east-1

# Docker Image
IMAGE_TAG=latest
EOF

    # Create deployment package
    cd /tmp
    tar -czf "zain_hms_deployment.tar.gz" -C "$DEPLOY_DIR" .
    
    echo -e "${GREEN}✅ Deployment package prepared${NC}"
}

# Function to setup server
setup_server() {
    echo -e "${YELLOW}🖥️  Setting up production server...${NC}"

    SSH_CMD="ssh -o StrictHostKeyChecking=no"
    if [ -n "$DEPLOY_KEY" ]; then
        SSH_CMD="$SSH_CMD -i $DEPLOY_KEY"
    fi

    SCP_CMD="scp -o StrictHostKeyChecking=no"
    if [ -n "$DEPLOY_KEY" ]; then
        SCP_CMD="$SCP_CMD -i $DEPLOY_KEY"
    fi

    # Copy server setup script
    $SCP_CMD "$PROJECT_DIR/scripts/setup-production-server.sh" "$SERVER_USER@$SERVER_IP:/tmp/"

    # Run server setup
    $SSH_CMD "$SERVER_USER@$SERVER_IP" "chmod +x /tmp/setup-production-server.sh && /tmp/setup-production-server.sh $DOMAIN"

    echo -e "${GREEN}✅ Server setup completed${NC}"
}

# Function to deploy application
deploy_application() {
    echo -e "${YELLOW}🚀 Deploying application to server...${NC}"

    SSH_CMD="ssh -o StrictHostKeyChecking=no"
    if [ -n "$DEPLOY_KEY" ]; then
        SSH_CMD="$SSH_CMD -i $DEPLOY_KEY"
    fi

    SCP_CMD="scp -o StrictHostKeyChecking=no"
    if [ -n "$DEPLOY_KEY" ]; then
        SCP_CMD="$SCP_CMD -i $DEPLOY_KEY"
    fi

    # Copy deployment package to server
    $SCP_CMD "/tmp/zain_hms_deployment.tar.gz" "$SERVER_USER@$SERVER_IP:/tmp/"

    # Deploy on server
    $SSH_CMD "$SERVER_USER@$SERVER_IP" << EOF
        set -e
        
        # Extract deployment package
        cd /opt/zain_hms
        tar -xzf /tmp/zain_hms_deployment.tar.gz
        
        # Set ownership
        chown -R zain-hms:zain-hms /opt/zain_hms
        
        # Check if .env.prod exists, if not create from template
        if [ ! -f .env.prod ]; then
            echo "⚠️  Creating .env.prod from template - PLEASE EDIT WITH ACTUAL VALUES!"
            cp .env.prod.template .env.prod
            chown zain-hms:zain-hms .env.prod
            chmod 600 .env.prod
            
            echo "❌ Please edit /opt/zain_hms/.env.prod with actual values before running deployment!"
            echo "Then run: sudo -u zain-hms /opt/zain_hms/deploy.sh"
            exit 1
        fi
        
        # Run deployment as zain-hms user
        sudo -u zain-hms ./deploy.sh
EOF

    echo -e "${GREEN}✅ Application deployed${NC}"
}

# Function to verify deployment
verify_deployment() {
    echo -e "${YELLOW}🔍 Verifying deployment...${NC}"

    SSH_CMD="ssh -o StrictHostKeyChecking=no"
    if [ -n "$DEPLOY_KEY" ]; then
        SSH_CMD="$SSH_CMD -i $DEPLOY_KEY"
    fi

    # Wait for services to be ready
    sleep 30

    # Check if containers are running
    CONTAINERS_STATUS=$($SSH_CMD "$SERVER_USER@$SERVER_IP" "cd /opt/zain_hms && docker-compose -f docker-compose.prod.yml ps --services --filter status=running | wc -l")
    
    if [ "$CONTAINERS_STATUS" -ge 3 ]; then
        echo -e "${GREEN}✅ All containers are running${NC}"
    else
        echo -e "${RED}❌ Some containers are not running${NC}"
        $SSH_CMD "$SERVER_USER@$SERVER_IP" "cd /opt/zain_hms && docker-compose -f docker-compose.prod.yml ps"
    fi

    # Test HTTP connectivity
    if curl -f "http://$SERVER_IP/health/" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Application is responding to HTTP requests${NC}"
    else
        echo -e "${RED}❌ Application is not responding${NC}"
    fi

    # Show final status
    echo -e "${BLUE}📊 Deployment Summary:${NC}"
    echo "• Server IP: $SERVER_IP"
    echo "• Domain: $DOMAIN"
    echo "• Environment: $ENVIRONMENT"
    echo "• Application URL: http://$SERVER_IP"
    if [ "$DOMAIN" != "localhost" ]; then
        echo "• Domain URL: http://$DOMAIN"
    fi

    echo -e "${GREEN}🎉 Deployment verification completed!${NC}"
}

# Function to cleanup
cleanup() {
    echo -e "${YELLOW}🧹 Cleaning up temporary files...${NC}"
    
    # Remove temporary files
    rm -rf "/tmp/zain_hms_deploy_"*
    rm -f "/tmp/zain_hms_deployment.tar.gz"
    
    echo -e "${GREEN}✅ Cleanup completed${NC}"
}

# Main function
main() {
    echo -e "${BLUE}🏥 ZAIN HMS Automated Deployment${NC}"
    echo "=================================="
    echo ""

    parse_args "$@"
    validate_prerequisites
    prepare_deployment
    setup_server
    
    # Deploy application (might fail if .env.prod needs configuration)
    if deploy_application; then
        verify_deployment
    else
        echo -e "${YELLOW}⚠️  Deployment requires manual configuration${NC}"
        echo -e "${YELLOW}Please SSH to the server and edit /opt/zain_hms/.env.prod${NC}"
        echo -e "${YELLOW}Then run: sudo -u zain-hms /opt/zain_hms/deploy.sh${NC}"
    fi
    
    cleanup
    
    echo ""
    echo -e "${GREEN}🎉 ZAIN HMS deployment process completed!${NC}"
}

# Handle script interruption
trap cleanup EXIT

# Run main function
main "$@"