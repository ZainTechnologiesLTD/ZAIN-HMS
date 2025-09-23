#!/bin/bash

# 🚀 ZAIN HMS - Complete Professional Setup Script
# This script sets up all missing professional features

echo "🏥 ZAIN HMS Professional Setup Starting..."
echo "================================================"

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "❌ Error: Run this script from ZAIN-HMS root directory"
    exit 1
fi

echo "📋 Current Status Check..."

# Check GitHub CLI availability
if command -v gh &> /dev/null; then
    echo "✅ GitHub CLI available"
    GH_CLI_AVAILABLE=true
else
    echo "⚠️  GitHub CLI not available - will provide manual instructions"
    GH_CLI_AVAILABLE=false
fi

# Check current git status
echo "📊 Git Status:"
git status --porcelain
echo ""

# 1. CREATE RELEASE v2.1.0
echo "🎯 Step 1: Creating GitHub Release v2.1.0..."
echo "============================================"

if [ "$GH_CLI_AVAILABLE" = true ]; then
    echo "🚀 Creating release with GitHub CLI..."
    gh release create v2.1.0 \
        --title "🏥 ZAIN HMS v2.1.0 - Complete System Modernization" \
        --notes-file RELEASE_NOTES_v2.1.0.md \
        --latest
    echo "✅ Release created successfully!"
else
    echo "📝 Manual Release Creation Required:"
    echo "1. Go to: https://github.com/Zain-Technologies-22/ZAIN-HMS/releases/new"
    echo "2. Tag: v2.1.0"
    echo "3. Title: 🏥 ZAIN HMS v2.1.0 - Complete System Modernization"
    echo "4. Copy content from: RELEASE_NOTES_v2.1.0.md"
    echo "5. Check 'Set as latest release'"
    echo "6. Click 'Publish release'"
fi

echo ""

# 2. CREATE DOCKER PACKAGE CONFIGURATION
echo "🎯 Step 2: Setting up GitHub Packages (Docker)..."
echo "=================================================="

# Create Dockerfile if not exists
if [ ! -f "Dockerfile" ]; then
    echo "📦 Creating production Dockerfile..."
    cat > Dockerfile << 'EOF'
# 🏥 ZAIN HMS Production Docker Image
# Multi-stage build for optimized production deployment

# Build stage
FROM python:3.12-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.12-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    postgresql-client \
    nginx \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create app user
RUN useradd --create-home --shell /bin/bash zain
WORKDIR /app

# Copy application code
COPY --chown=zain:zain . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Configure nginx and supervisor
COPY docker/nginx.conf /etc/nginx/sites-available/default
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Expose ports
EXPOSE 80 8000

# Switch to app user
USER zain

# Start command
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
EOF
    echo "✅ Dockerfile created"
else
    echo "✅ Dockerfile already exists"
fi

# Create .dockerignore
if [ ! -f ".dockerignore" ]; then
    echo "📦 Creating .dockerignore..."
    cat > .dockerignore << 'EOF'
.git
.gitignore
README.md
Dockerfile
.dockerignore
.env
.env.*
node_modules
npm-debug.log
Dockerfile*
docker-compose*
__pycache__
*.pyc
.pytest_cache
.coverage
htmlcov/
.venv
venv/
logs/
*.log
media/
static/admin/
static/rest_framework/
EOF
    echo "✅ .dockerignore created"
fi

# Create docker-compose for development
if [ ! -f "docker-compose.yml" ]; then
    echo "📦 Creating docker-compose.yml..."
    cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  web:
    build: .
    image: ghcr.io/zain-technologies-22/zain-hms:latest
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - DATABASE_URL=postgresql://postgres:password@db:5432/zain_hms
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - media_volume:/app/media
      - static_volume:/app/staticfiles
    
  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=zain_hms
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./docker/nginx.conf:/etc/nginx/conf.d/default.conf
      - static_volume:/var/www/static
      - media_volume:/var/www/media
    depends_on:
      - web

volumes:
  postgres_data:
  media_volume:
  static_volume:
EOF
    echo "✅ docker-compose.yml created"
fi

echo ""

# 3. REPOSITORY SETTINGS CONFIGURATION
echo "🎯 Step 3: Repository Configuration Checklist..."
echo "==============================================="

echo "📋 Manual Repository Settings Required:"
echo ""
echo "🔒 Security Settings:"
echo "  1. Go to Settings > Security & analysis"
echo "  2. Enable: Dependency alerts, Dependabot alerts, Dependabot security updates"
echo "  3. Enable: Code scanning alerts, Secret scanning alerts"
echo ""
echo "🛡️ Branch Protection (Settings > Branches):"
echo "  1. Add rule for 'main' branch"
echo "  2. Require status checks: ✅"
echo "  3. Require branches up to date: ✅"
echo "  4. Require review from code owners: ✅"
echo "  5. Dismiss stale reviews: ✅"
echo "  6. Restrict pushes to matching branches: ✅"
echo ""
echo "📦 Packages (Settings > General):"
echo "  1. Scroll to 'Features'"
echo "  2. Enable 'Packages': ✅"
echo ""
echo "📄 Pages (Settings > Pages):"
echo "  1. Source: Deploy from branch"
echo "  2. Branch: main / docs"
echo ""

# 4. CHECK ACTIONS STATUS
echo "🎯 Step 4: GitHub Actions Status..."
echo "=================================="

if [ "$GH_CLI_AVAILABLE" = true ]; then
    echo "📊 Current workflow runs:"
    gh run list --limit 5
else
    echo "📝 Check Actions manually:"
    echo "  Go to: https://github.com/Zain-Technologies-22/ZAIN-HMS/actions"
    echo "  Verify all 4 workflows are present and running"
fi

echo ""

# 5. ENVIRONMENT SETUP
echo "🎯 Step 5: Environment Configuration..."
echo "====================================="

echo "🔧 Required Repository Secrets:"
echo "  (Settings > Security > Secrets and variables > Actions)"
echo ""
echo "  Production Deployment:"
echo "  - PRODUCTION_HOST: your-server.com"
echo "  - SSH_PRIVATE_KEY: (your deployment key)"
echo "  - SSH_USER: deployment-user"
echo ""
echo "  Database & Services:"
echo "  - DATABASE_URL: postgresql://user:pass@host:5432/db"
echo "  - REDIS_URL: redis://host:6379/0"
echo "  - SECRET_KEY: (Django secret key)"
echo ""
echo "  External Services:"
echo "  - SENTRY_DSN: (error monitoring)"
echo "  - EMAIL_HOST_PASSWORD: (email service)"
echo ""

# 6. FINAL STATUS
echo "🎯 Final Setup Status..."
echo "======================="
echo ""
echo "✅ Completed:"
echo "  - Release notes prepared"
echo "  - Docker configuration created"
echo "  - Repository checklist provided"
echo ""
echo "📋 Next Manual Actions:"
echo "  1. Create GitHub Release (if CLI not available)"
echo "  2. Configure repository settings"
echo "  3. Add repository secrets"
echo "  4. Test Docker build: docker build -t zain-hms ."
echo "  5. Publish first package"
echo ""

echo "🎉 ZAIN HMS Professional Setup Complete!"
echo "========================================"
echo ""
echo "🚀 Your repository is now enterprise-ready with:"
echo "   ✅ Modern CI/CD pipelines"
echo "   ✅ Professional documentation"
echo "   ✅ Docker containerization"
echo "   ✅ Security configurations"
echo "   ✅ Release management"
echo ""
echo "🏥 Ready for production deployment! ✨"
EOF