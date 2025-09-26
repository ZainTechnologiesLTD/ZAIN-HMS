#!/bin/bash
# 📊 Branch status checker and management tool
# Usage: ./scripts/branch-status.sh

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
NC='\033[0m'

clear
echo -e "${PURPLE}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                  🏥 ZAIN HMS Branch Status                ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Current branch
CURRENT_BRANCH=$(git branch --show-current)
echo -e "${BLUE}📍 Current Branch: ${GREEN}$CURRENT_BRANCH${NC}"

# Check for uncommitted changes
if [ ! -z "$(git status --porcelain)" ]; then
    echo -e "${RED}⚠️  Uncommitted changes detected:${NC}"
    git status --short
else
    echo -e "${GREEN}✅ Working directory clean${NC}"
fi

echo ""

# Branch information
echo -e "${BLUE}📋 Branch Information:${NC}"
echo -e "${BLUE}├── Local Branches:${NC}"
git branch | sed 's/^/│   /'

echo -e "${BLUE}├── Remote Branches:${NC}"
git branch -r | sed 's/^/│   /'

echo ""

# Check differences between branches
echo -e "${BLUE}📊 Branch Comparison:${NC}"

# Development ahead of main
DEV_AHEAD=$(git rev-list --count main..development)
if [ "$DEV_AHEAD" -gt 0 ]; then
    echo -e "${YELLOW}📦 Development is $DEV_AHEAD commits ahead of main${NC}"
    echo -e "${BLUE}├── Recent development commits:${NC}"
    git log main..development --oneline | head -5 | sed 's/^/│   /'
else
    echo -e "${GREEN}✅ Development and main are in sync${NC}"
fi

echo ""

# Main ahead of development (shouldn't happen in normal workflow)
MAIN_AHEAD=$(git rev-list --count development..main)
if [ "$MAIN_AHEAD" -gt 0 ]; then
    echo -e "${RED}⚠️  Main is $MAIN_AHEAD commits ahead of development (unusual!)${NC}"
    echo -e "${RED}├── Main-only commits:${NC}"
    git log development..main --oneline | sed 's/^/│   /'
fi

echo ""

# Show recent commits on current branch
echo -e "${BLUE}📜 Recent commits on $CURRENT_BRANCH:${NC}"
git log --oneline -5 | sed 's/^/   /'

echo ""

# Quick actions menu
echo -e "${PURPLE}🔧 Quick Actions:${NC}"
echo "1. Push current changes to development"
echo "2. Deploy development → main"  
echo "3. Switch to development"
echo "4. Switch to main"
echo "5. Create new feature branch"
echo "6. Exit"

read -p "Choose action (1-6): " action

case $action in
    1)
        if [ "$CURRENT_BRANCH" != "development" ]; then
            git checkout development
        fi
        ./scripts/push-to-development.sh
        ;;
    2)
        ./scripts/deploy-to-main.sh
        ;;
    3)
        git checkout development
        echo -e "${GREEN}✅ Switched to development branch${NC}"
        ;;
    4)
        git checkout main
        echo -e "${GREEN}✅ Switched to main branch${NC}"
        ;;
    5)
        read -p "Enter feature branch name: " feature_name
        git checkout development
        git checkout -b "feature/$feature_name"
        echo -e "${GREEN}✅ Created and switched to feature/$feature_name${NC}"
        ;;
    6)
        echo -e "${BLUE}👋 Goodbye!${NC}"
        ;;
    *)
        echo -e "${RED}Invalid option${NC}"
        ;;
esac