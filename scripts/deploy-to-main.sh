#!/bin/bash
# 🚀 Deploy development to main (production)
# Usage: ./scripts/deploy-to-main.sh

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 Deploying development to main (production)...${NC}"

# Ensure clean working directory
if [ ! -z "$(git status --porcelain)" ]; then
    echo -e "${RED}⚠️  You have uncommitted changes. Please commit or stash them first.${NC}"
    git status --short
    exit 1
fi

# Switch to main
echo -e "${BLUE}📂 Switching to main branch...${NC}"
git checkout main

# Fetch latest changes
git fetch origin

# Check if development has new commits
BEHIND=$(git rev-list --count main..development)

if [ "$BEHIND" -eq 0 ]; then
    echo -e "${GREEN}✅ Main is already up to date with development${NC}"
    
    # Still push to make sure remote is synced
    git push origin main
    exit 0
fi

echo -e "${YELLOW}📦 Development is $BEHIND commits ahead of main${NC}"
echo -e "${BLUE}🔄 Merging development → main...${NC}"

# Show what will be merged
echo -e "\n${BLUE}📋 Changes to be deployed:${NC}"
git log main..development --oneline

# Confirm deployment
read -p "Deploy these changes to production? (y/N): " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}⚠️  Deployment cancelled${NC}"
    git checkout development
    exit 0
fi

# Merge development
git merge development --no-ff -m "chore: deploy development to main - $(date '+%Y-%m-%d %H:%M')"

# Push to production
echo -e "${BLUE}📤 Pushing to production...${NC}"
git push origin main

echo -e "${GREEN}✅ Successfully deployed to production (main branch)!${NC}"
echo -e "${BLUE}🌐 Live at: https://github.com/ZainTechnologiesLTD/ZAIN-HMS${NC}"

# Show deployment summary
echo -e "\n${BLUE}📊 Deployment summary:${NC}"
git log main --oneline -3

# Switch back to development for continued work
echo -e "${BLUE}🔄 Switching back to development branch...${NC}"
git checkout development