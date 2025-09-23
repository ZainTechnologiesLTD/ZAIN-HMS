# Push ZAIN HMS to GitHub Repository
#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Repository configuration
REPO_ORG="Zain-Technologies-22"
REPO_NAME="ZAIN-HMS"
REPO_URL="https://github.com/$REPO_ORG/$REPO_NAME.git"

# Display banner
echo -e "${PURPLE}"
echo "╔═══════════════════════════════════════════════════╗"
echo "║         ZAIN HMS - Push to GitHub Repository     ║"
echo "║     Enhanced with Deployment & Update System     ║"
echo "╚═══════════════════════════════════════════════════╝"
echo -e "${NC}"

# Function to log messages
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

# Check if we're in the right directory
if [ ! -f "manage.py" ] || [ ! -d "zain_hms" ]; then
    error "This script must be run from the ZAIN HMS project root directory"
fi

# Check if git is initialized
if [ ! -d ".git" ]; then
    log "Initializing git repository..."
    git init
    git remote add origin $REPO_URL
else
    # Check if remote is set correctly
    CURRENT_REMOTE=$(git remote get-url origin 2>/dev/null)
    if [ "$CURRENT_REMOTE" != "$REPO_URL" ]; then
        log "Updating git remote URL..."
        git remote set-url origin $REPO_URL
    fi
fi

# Check git status
log "Checking current git status..."
git status

# Add all new files
log "Adding new deployment and update system files..."
git add .

# Create comprehensive commit message
COMMIT_MESSAGE="🚀 Enhanced ZAIN HMS with Complete Deployment System

✨ New Features:
- Automatic update notifications with in-app display
- Zero-downtime deployment with database migration safety  
- Comprehensive version management with semantic versioning
- Maintenance mode during updates with elegant UI
- CI/CD pipeline with automated testing and deployment
- Docker containerization for production deployment
- Database backup and rollback capabilities

🔧 Technical Improvements:
- Django management commands for system maintenance
- Migration validation and safety checks
- Cache clearing and search index updates
- Post-migration task automation
- Enhanced error handling and logging
- Health check endpoints for monitoring

🏥 Hospital Management Enhancements:
- Improved multi-tenant architecture
- Enhanced security and audit trails
- Better mobile responsiveness
- AI clinical decision support updates
- Performance optimizations

📋 Deployment Ready:
- Production Docker configuration
- Automated backup and restore
- Server environment setup scripts
- Comprehensive documentation
- Monitoring and health checks

Version: 2.1.0 - September 2025 Release"

# Show what will be committed
echo -e "\n${YELLOW}📋 Files to be committed:${NC}"
git diff --cached --name-status

echo -e "\n${YELLOW}📝 Commit message:${NC}"
echo "$COMMIT_MESSAGE"

# Ask for confirmation
echo -e "\n${BLUE}🤔 Do you want to proceed with this commit and push? (y/N)${NC}"
read -r confirmation

if [[ $confirmation =~ ^[Yy]$ ]]; then
    # Commit changes
    log "Committing changes..."
    git commit -m "$COMMIT_MESSAGE"
    
    if [ $? -eq 0 ]; then
        success "Changes committed successfully"
        
        # Get current branch
        CURRENT_BRANCH=$(git branch --show-current)
        log "Current branch: $CURRENT_BRANCH"
        
        # Push to GitHub
        log "Pushing to GitHub repository..."
        git push -u origin $CURRENT_BRANCH
        
        if [ $? -eq 0 ]; then
            success "Successfully pushed to GitHub!"
            echo ""
            echo -e "${GREEN}🎉 ZAIN HMS Enhanced Deployment System Uploaded!${NC}"
            echo ""
            echo -e "${BLUE}📋 What was added:${NC}"
            echo "✅ Complete automatic update notification system"
            echo "✅ Zero-downtime deployment with migration safety"
            echo "✅ Professional version management (v2.1.0)"
            echo "✅ Docker production configuration"
            echo "✅ CI/CD pipeline with automated testing"
            echo "✅ Database backup and rollback system"
            echo "✅ Maintenance mode with elegant UI"
            echo "✅ Health monitoring and checks"
            echo ""
            echo -e "${BLUE}🔗 Repository: https://github.com/$REPO_ORG/$REPO_NAME${NC}"
            echo -e "${BLUE}📊 View Changes: https://github.com/$REPO_ORG/$REPO_NAME/commits/$CURRENT_BRANCH${NC}"
            echo ""
            echo -e "${PURPLE}🚀 Next Steps:${NC}"
            echo "1. Set up your production Ubuntu server"
            echo "2. Configure GitHub repository secrets:"
            echo "   - HMS_SECRET (already set: MehediBabo@1521)"
            echo "   - DOCKER_USERNAME (your Docker Hub username)"
            echo "   - DOCKER_PASSWORD (your Docker Hub password)"
            echo "   - SERVER_HOST (your production server IP)"
            echo "   - SERVER_USER (your server username)"
            echo "   - SERVER_SSH_KEY (your SSH private key)"
            echo "3. Test the deployment pipeline"
            echo "4. Run your release manager: ./scripts/release_manager.sh"
            echo ""
            echo -e "${GREEN}🏥 Your ZAIN HMS is now enterprise-ready with professional deployment capabilities!${NC}"
            
        else
            error "Failed to push to GitHub. Please check your credentials and try again."
        fi
    else
        error "Failed to commit changes"
    fi
else
    log "Push cancelled by user"
    echo -e "${YELLOW}💡 Tip: You can run this script again when ready to push${NC}"
fi

echo -e "\n${BLUE}📝 Git Status:${NC}"
git status --short