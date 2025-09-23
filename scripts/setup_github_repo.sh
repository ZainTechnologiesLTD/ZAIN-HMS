# GitHub Repository Setup Script
# This script helps you create and configure your private GitHub repository

#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Repository configuration
REPO_NAME="ZAIN-HMS"
REPO_DESCRIPTION="ZAIN Hospital Management System - Private Repository"
GITHUB_USERNAME="MehediHossain95"
GITHUB_ORG="Zain-Technologies-22"  # Organization name

echo -e "${BLUE}🚀 GitHub Repository Setup for ZAIN HMS${NC}"
echo "=============================================="

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ GitHub CLI is not installed${NC}"
    echo "Please install GitHub CLI first:"
    echo "https://cli.github.com/"
    exit 1
fi

# Check if user is logged in to GitHub CLI
if ! gh auth status &> /dev/null; then
    echo -e "${YELLOW}⚠️  You're not logged in to GitHub CLI${NC}"
    echo "Please login first:"
    echo "gh auth login"
    exit 1
fi

echo -e "${GREEN}✅ GitHub CLI is ready${NC}"

# Check if repository already exists
echo -e "${BLUE}🔍 Checking if repository exists${NC}"

if gh repo view ${GITHUB_ORG}/${REPO_NAME} &> /dev/null; then
    echo -e "${GREEN}✅ Repository ${GITHUB_ORG}/${REPO_NAME} already exists${NC}"
    REPO_EXISTS=true
else
    # Create private repository in organization
    echo -e "${BLUE}📁 Creating private repository: ${REPO_NAME} in ${GITHUB_ORG}${NC}"
    
    gh repo create ${GITHUB_ORG}/${REPO_NAME} \
        --private \
        --description "${REPO_DESCRIPTION}" \
        --gitignore Python \
        --license MIT
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Repository created successfully${NC}"
        REPO_EXISTS=true
    else
        echo -e "${RED}❌ Failed to create repository${NC}"
        exit 1
    fi
fi

# Initialize git repository and set remote
if [ ! -d ".git" ]; then
    echo -e "${BLUE}� Initializing git repository${NC}"
    git init
    git remote add origin https://github.com/${GITHUB_ORG}/${REPO_NAME}.git
else
    # Update remote if it's different
    CURRENT_REMOTE=$(git remote get-url origin 2>/dev/null)
    EXPECTED_REMOTE="https://github.com/${GITHUB_ORG}/${REPO_NAME}.git"
    
    if [ "$CURRENT_REMOTE" != "$EXPECTED_REMOTE" ]; then
        echo -e "${BLUE}🔧 Updating git remote${NC}"
        git remote set-url origin $EXPECTED_REMOTE
    fi
fi

# Create branch protection rules
echo -e "${BLUE}🛡️  Setting up branch protection${NC}"

# Create main branch if it doesn't exist
git checkout -b main 2>/dev/null || git checkout main

# Set up branch protection for main branch
gh api repos/:owner/:repo/branches/main/protection \
    --method PUT \
    --field required_status_checks='{"strict":true,"contexts":["ci/tests","ci/build"]}' \
    --field enforce_admins=true \
    --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true}' \
    --field restrictions=null \
    2>/dev/null || echo -e "${YELLOW}⚠️  Branch protection will be set up after first push${NC}"

# Create development branch
echo -e "${BLUE}🌱 Creating development branch${NC}"
git checkout -b development 2>/dev/null || git checkout development

# Create .github directory structure
echo -e "${BLUE}📁 Creating GitHub workflows directory${NC}"
mkdir -p .github/workflows
mkdir -p .github/ISSUE_TEMPLATE
mkdir -p .github/PULL_REQUEST_TEMPLATE

# Create issue templates
cat > .github/ISSUE_TEMPLATE/bug_report.md << EOF
---
name: Bug report
about: Create a report to help us improve ZAIN HMS
title: '[BUG] '
labels: bug
assignees: ''
---

**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment:**
- Browser [e.g. chrome, safari]
- Version [e.g. 22]
- OS: [e.g. iOS]

**Additional context**
Add any other context about the problem here.
EOF

cat > .github/ISSUE_TEMPLATE/feature_request.md << EOF
---
name: Feature request
about: Suggest an idea for ZAIN HMS
title: '[FEATURE] '
labels: enhancement
assignees: ''
---

**Is your feature request related to a problem? Please describe.**
A clear and concise description of what the problem is.

**Describe the solution you'd like**
A clear and concise description of what you want to happen.

**Describe alternatives you've considered**
A clear and concise description of any alternative solutions or features you've considered.

**Additional context**
Add any other context or screenshots about the feature request here.
EOF

# Create pull request template
cat > .github/PULL_REQUEST_TEMPLATE.md << EOF
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] I have tested my changes locally
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes

## Checklist
- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
EOF

# Create repository secrets documentation
cat > .github/REPOSITORY_SECRETS.md << EOF
# Required Repository Secrets

To enable CI/CD pipeline, add these secrets to your repository:

## Required Secrets:
\`\`\`
DOCKER_REGISTRY_URL=your-registry-url
DOCKER_USERNAME=your-docker-username
DOCKER_PASSWORD=your-docker-password
GITHUB_TOKEN=your-github-token
SERVER_HOST=your-production-server-ip
SERVER_USER=your-server-username
SERVER_SSH_KEY=your-private-ssh-key
DATABASE_URL=your-production-database-url
SECRET_KEY=your-django-secret-key
\`\`\`

## How to add secrets:
1. Go to repository Settings
2. Click on "Secrets and variables" → "Actions"
3. Click "New repository secret"
4. Add each secret with its value

## Optional Secrets:
\`\`\`
SLACK_WEBHOOK_URL=your-slack-webhook-for-notifications
EMAIL_HOST_PASSWORD=smtp-password-for-notifications
\`\`\`
EOF

# Create README.md
cat > README.md << EOF
# ZAIN Hospital Management System

A comprehensive hospital management system built with Django and modern web technologies.

## 🏥 Features

- **Patient Management**: Complete patient registration and medical records
- **Appointment System**: Online booking and schedule management
- **Billing & Invoicing**: Automated billing with payment tracking
- **Inventory Management**: Medicine and equipment tracking
- **Reports & Analytics**: Comprehensive reporting dashboard
- **Multi-language Support**: Available in multiple languages
- **Role-based Access**: Secure access control for different user types

## 🚀 Technology Stack

- **Backend**: Django 4.x, Python 3.11+
- **Database**: PostgreSQL 15+
- **Frontend**: HTML5, CSS3, JavaScript, Alpine.js
- **Caching**: Redis
- **Containerization**: Docker & Docker Compose
- **CI/CD**: GitHub Actions
- **Web Server**: Nginx

## 📋 Requirements

- Python 3.11+
- PostgreSQL 15+
- Redis 6+
- Docker & Docker Compose (for production)

## 🛠️ Installation

### Development Setup

1. Clone the repository:
\`\`\`bash
git clone https://github.com/${GITHUB_ORG}/${REPO_NAME}.git
cd ${REPO_NAME}
\`\`\`

2. Create virtual environment:
\`\`\`bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
\`\`\`

3. Install dependencies:
\`\`\`bash
pip install -r requirements.txt
\`\`\`

4. Setup environment variables:
\`\`\`bash
cp .env.example .env
# Edit .env with your configuration
\`\`\`

5. Run migrations:
\`\`\`bash
python manage.py migrate
\`\`\`

6. Create superuser:
\`\`\`bash
python manage.py createsuperuser
\`\`\`

7. Start development server:
\`\`\`bash
python manage.py runserver
\`\`\`

### Production Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed production deployment instructions.

## 🔄 CI/CD Pipeline

This project includes automated CI/CD pipeline with:

- **Continuous Integration**: Automated testing on every pull request
- **Security Scanning**: Code security analysis
- **Docker Build**: Automated Docker image creation
- **Deployment**: Zero-downtime deployment to production
- **Health Checks**: Automated post-deployment verification

## 📖 Documentation

- [API Documentation](docs/api.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Contributing Guidelines](CONTRIBUTING.md)
- [Troubleshooting](docs/troubleshooting.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (\`git checkout -b feature/amazing-feature\`)
3. Commit your changes (\`git commit -m 'Add some amazing feature'\`)
4. Push to the branch (\`git push origin feature/amazing-feature\`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter any issues or need support:

1. Check the [documentation](docs/)
2. Search existing [issues](https://github.com/${GITHUB_ORG}/${REPO_NAME}/issues)
3. Create a new issue if needed

## 🏆 Acknowledgments

- Django Team for the excellent web framework
- Contributors and maintainers
- Healthcare professionals who provided requirements and feedback

---

**Note**: This is a private repository. Please ensure you have proper authorization before accessing or contributing.
EOF

echo -e "${GREEN}✅ Repository structure created successfully${NC}"

# Setup repository secrets
echo -e "${BLUE}🔐 Setting up repository secrets${NC}"

# Set the HMS_SECRET that you provided
echo -e "${BLUE}   Adding HMS_SECRET...${NC}"
echo "MehediBabo@1521" | gh secret set HMS_SECRET --repo ${GITHUB_ORG}/${REPO_NAME}

if [ $? -eq 0 ]; then
    echo -e "${GREEN}   ✅ HMS_SECRET added successfully${NC}"
else
    echo -e "${YELLOW}   ⚠️  Failed to add HMS_SECRET. You can add it manually later.${NC}"
fi

# Add other essential secrets (you'll need to update these values)
echo -e "${BLUE}   Setting up placeholder secrets...${NC}"

# Django Secret Key (generate a new one for production)
DJANGO_SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())' 2>/dev/null || echo "django-insecure-change-this-in-production-$(date +%s)")
echo "$DJANGO_SECRET_KEY" | gh secret set DJANGO_SECRET_KEY --repo ${GITHUB_ORG}/${REPO_NAME} 2>/dev/null

# Database URL placeholder
echo "postgresql://postgres:password@localhost:5432/zain_hms" | gh secret set DATABASE_URL --repo ${GITHUB_ORG}/${REPO_NAME} 2>/dev/null

# Docker Hub credentials placeholders (you'll need to update these)
echo "your-dockerhub-username" | gh secret set DOCKER_USERNAME --repo ${GITHUB_ORG}/${REPO_NAME} 2>/dev/null
echo "your-dockerhub-password" | gh secret set DOCKER_PASSWORD --repo ${GITHUB_ORG}/${REPO_NAME} 2>/dev/null

# Server deployment placeholders (you'll need to update these)
echo "your-server-ip" | gh secret set SERVER_HOST --repo ${GITHUB_ORG}/${REPO_NAME} 2>/dev/null
echo "ubuntu" | gh secret set SERVER_USER --repo ${GITHUB_ORG}/${REPO_NAME} 2>/dev/null

echo -e "${GREEN}   ✅ Basic secrets configured${NC}"
echo -e "${YELLOW}   ⚠️  Please update the placeholder secrets with your actual values${NC}"

# Add all files to git
echo -e "${BLUE}📤 Adding files to git${NC}"
git add .
git commit -m "Initial commit: ZAIN HMS setup with CI/CD pipeline"

# Push to GitHub
echo -e "${BLUE}🚀 Pushing to GitHub${NC}"
git push -u origin development

# Switch to main and push
git checkout main
git merge development
git push -u origin main

echo -e "${GREEN}✅ Repository setup completed successfully!${NC}"
echo ""
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo "1. ✅ Repository configured with your organization: ${GITHUB_ORG}"
echo "2. ✅ HMS_SECRET has been added to repository secrets"
echo "3. 🔧 Update placeholder secrets in GitHub Settings > Secrets and variables > Actions:"
echo "   - DOCKER_USERNAME (your Docker Hub username)"
echo "   - DOCKER_PASSWORD (your Docker Hub password)"
echo "   - SERVER_HOST (your production server IP)"
echo "   - SERVER_USER (your server username, usually 'ubuntu')"
echo "   - SERVER_SSH_KEY (your private SSH key for server access)"
echo "4. Review and update the CI/CD pipeline in .github/workflows/"
echo "5. Test the deployment pipeline"
echo ""
echo -e "${BLUE}🔗 Repository URL: https://github.com/${GITHUB_ORG}/${REPO_NAME}${NC}"
echo -e "${BLUE}🔐 Secrets URL: https://github.com/${GITHUB_ORG}/${REPO_NAME}/settings/secrets/actions${NC}"
EOF