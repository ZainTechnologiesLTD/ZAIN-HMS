#!/bin/bash
# 🔄 Push changes to development branch
# Usage: ./scripts/push-to-development.sh

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🔄 Pushing changes to development branch...${NC}"

# Ensure we're on development branch
git checkout development

# Check for changes
if [ -z "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}⚠️  No changes detected to commit${NC}"
    exit 0
fi

# Show status
git status --short

# Add all changes
git add .

# Get commit message
read -p "Enter commit message: " message
if [ -z "$message" ]; then
    message="chore: update development branch - $(date '+%Y-%m-%d %H:%M')"
fi

# Commit changes
git commit -m "$message"

# Push to development
git push origin development

echo -e "${GREEN}✅ Changes pushed to development branch!${NC}"
echo -e "${BLUE}📝 To deploy to production, run: ./scripts/deploy-to-main.sh${NC}"

# Show current status
echo -e "\n${BLUE}📊 Current branch status:${NC}"
git log development --oneline -3