#!/bin/bash
# 🚀 Push SSL fixes and Docker improvements to GitHub
# This script commits all changes and deploys to development and main branches

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}🚀 ZAIN HMS - SSL Fixes Deployment${NC}"
echo "==============================================="

# Check if we're in a git repository
if [ ! -d .git ]; then
    echo -e "${RED}❌ Not in a git repository${NC}"
    exit 1
fi

# Show current status
echo -e "${BLUE}📊 Current Git Status:${NC}"
git status --short

echo ""
echo -e "${YELLOW}📝 Changes to commit:${NC}"
echo "1. Fixed SSL certificate issues in Docker build"
echo "2. Added trusted hosts configuration for pip"
echo "3. Enhanced Docker build with retry mechanisms"
echo "4. Updated installation script with SSL-aware builds"
echo "5. Added ca-certificates and SSL handling in Dockerfile"

read -p "Continue with commit and push? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}❌ Deployment cancelled${NC}"
    exit 0
fi

# Check current branch
CURRENT_BRANCH=$(git branch --show-current)
echo -e "${BLUE}📍 Current branch: $CURRENT_BRANCH${NC}"

# Stage all changes
echo -e "${YELLOW}📋 Staging changes...${NC}"
git add .

# Commit with descriptive message
echo -e "${YELLOW}💾 Creating commit...${NC}"
git commit -m "🔧 Fix SSL certificate issues in Docker build

- Added trusted hosts configuration for pip installations
- Enhanced Dockerfile with ca-certificates and SSL handling
- Added retry mechanisms for package installation
- Updated Docker build process to handle SSL errors
- Improved installation script with SSL-aware builds
- Added fallback build options for network issues

Fixes Docker build failures with cryptography package
SSL certificate errors during container deployment"

# Push to current branch first
echo -e "${YELLOW}⬆️  Pushing to $CURRENT_BRANCH...${NC}"
git push origin "$CURRENT_BRANCH"

# Switch to development branch if not already there
if [ "$CURRENT_BRANCH" != "development" ]; then
    echo -e "${YELLOW}🔄 Switching to development branch...${NC}"
    git checkout development
    git pull origin development
    
    echo -e "${YELLOW}🔄 Merging changes to development...${NC}"
    git merge "$CURRENT_BRANCH" --no-ff -m "Merge SSL fixes from $CURRENT_BRANCH"
fi

# Push to development
echo -e "${YELLOW}⬆️  Pushing to development...${NC}"
git push origin development

# Switch to main branch and merge
echo -e "${YELLOW}🔄 Switching to main branch...${NC}"
git checkout main
git pull origin main

echo -e "${YELLOW}🔄 Merging development to main...${NC}"
git merge development --no-ff -m "Release: SSL fixes and Docker improvements

- Fixed SSL certificate issues in Docker builds
- Enhanced container build process with retry mechanisms
- Improved installation script for SSL-aware deployments
- Added trusted hosts configuration for secure package installation

Version: $(date +%Y.%m.%d)"

# Push to main
echo -e "${YELLOW}⬆️  Pushing to main...${NC}"
git push origin main

# Create a release tag
TAG_VERSION="v$(date +%Y.%m.%d)-ssl-fixes"
echo -e "${YELLOW}🏷️  Creating release tag: $TAG_VERSION${NC}"
git tag -a "$TAG_VERSION" -m "SSL Fixes Release

- Fixed Docker build SSL certificate issues
- Enhanced pip installation with trusted hosts
- Improved container build reliability
- Added retry mechanisms for network issues

Date: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"

git push origin "$TAG_VERSION"

# Go back to original branch
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo -e "${YELLOW}🔄 Returning to $CURRENT_BRANCH...${NC}"
    git checkout "$CURRENT_BRANCH"
fi

echo ""
echo -e "${GREEN}✅ Successfully deployed SSL fixes!${NC}"
echo ""
echo -e "${CYAN}📋 Summary:${NC}"
echo -e "  🔧 Fixed SSL certificate issues in Docker build"
echo -e "  📦 Enhanced pip installation with trusted hosts"
echo -e "  🔄 Added retry mechanisms for build failures"
echo -e "  🚀 Updated installation script with SSL-aware builds"
echo -e "  🏷️  Created release tag: $TAG_VERSION"
echo ""
echo -e "${BLUE}🌐 GitHub Repository:${NC}"
echo "  Development: https://github.com/ZainTechnologiesLTD/ZAIN-HMS/tree/development"
echo "  Main: https://github.com/ZainTechnologiesLTD/ZAIN-HMS"
echo "  Release: https://github.com/ZainTechnologiesLTD/ZAIN-HMS/releases/tag/$TAG_VERSION"
echo ""
echo -e "${GREEN}🎉 Ready for deployment! The updated installation script can now handle SSL issues automatically.${NC}"