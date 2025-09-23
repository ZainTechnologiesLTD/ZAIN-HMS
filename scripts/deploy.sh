#!/bin/bash
# ZAIN HMS Deployment Script
# Usage: ./deploy.sh [VERSION] [IMAGE]

set -euo pipefail

VERSION=${1:-latest}
IMAGE=${2:-"ghcr.io/yourusername/zain-hms:$VERSION"}
APP_NAME="zain-hms"
DEPLOY_DIR="/opt/zain-hms"
BACKUP_DIR="/opt/backups/zain-hms"
LOG_FILE="/var/log/zain-hms-deploy.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root for security reasons"
fi

# Create directories if they don't exist
sudo mkdir -p "$BACKUP_DIR" "$DEPLOY_DIR"
sudo chown -R $USER:$USER "$BACKUP_DIR" "$DEPLOY_DIR"

log "Starting deployment of ZAIN HMS version: $VERSION"

# Pre-deployment checks
log "Running pre-deployment checks..."

# Check Docker
if ! command -v docker &> /dev/null; then
    error "Docker is not installed"
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    error "Docker Compose is not installed"
fi

# Check if previous deployment exists
if docker ps -q -f name="$APP_NAME" | grep -q .; then
    log "Previous deployment found. Preparing for update..."
    
    # Create backup
    log "Creating database backup..."
    BACKUP_FILE="$BACKUP_DIR/db_backup_$(date +%Y%m%d_%H%M%S).sql"
    docker exec zain-hms-db pg_dump -U postgres zain_hms > "$BACKUP_FILE" || warning "Database backup failed"
    
    # Backup media files
    log "Backing up media files..."
    MEDIA_BACKUP="$BACKUP_DIR/media_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
    tar -czf "$MEDIA_BACKUP" -C "$DEPLOY_DIR" media/ || warning "Media backup failed"
    
    success "Backups created successfully"
fi

# Pull new image
log "Pulling new Docker image: $IMAGE"
docker pull "$IMAGE" || error "Failed to pull Docker image"

# Navigate to deployment directory
cd "$DEPLOY_DIR"

# Create/update docker-compose.yml
log "Updating Docker Compose configuration..."
cat > docker-compose.prod.yml << EOF
version: '3.8'

services:
  app:
    image: $IMAGE
    container_name: ${APP_NAME}-app
    restart: unless-stopped
    environment:
      - DJANGO_SETTINGS_MODULE=zain_hms.production_settings
      - DATABASE_URL=postgres://postgres:secure_password@db:5432/zain_hms
      - REDIS_URL=redis://redis:6379/0
      - VERSION=$VERSION
    volumes:
      - ./media:/app/media
      - ./logs:/app/logs
      - ./static:/app/staticfiles
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    networks:
      - zain-hms-network

  db:
    image: postgres:15
    container_name: ${APP_NAME}-db
    restart: unless-stopped
    environment:
      - POSTGRES_DB=zain_hms
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    networks:
      - zain-hms-network

  redis:
    image: redis:7-alpine
    container_name: ${APP_NAME}-redis
    restart: unless-stopped
    networks:
      - zain-hms-network

  nginx:
    image: nginx:alpine
    container_name: ${APP_NAME}-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - ./static:/var/www/static:ro
      - ./media:/var/www/media:ro
    depends_on:
      - app
    networks:
      - zain-hms-network

volumes:
  postgres_data:

networks:
  zain-hms-network:
    driver: bridge
EOF

# Run database migrations (if needed)
log "Checking for database migrations..."

# First validate migrations for safety
log "Validating migrations for safety..."
if docker-compose -f docker-compose.prod.yml run --rm app python manage.py validate_migrations --dry-run --check-backward-compatibility; then
    log "Migration validation passed"
else
    warning "Migration validation found potential issues. Proceeding with caution..."
fi

# Check if there are pending migrations
PENDING_MIGRATIONS=$(docker-compose -f docker-compose.prod.yml run --rm app python manage.py showmigrations --plan | grep -c '\[ \]' || echo "0")

if [ "$PENDING_MIGRATIONS" -gt 0 ]; then
    log "Found $PENDING_MIGRATIONS pending migrations. Running migrations..."
    
    # Put application in maintenance mode
    log "Enabling maintenance mode..."
    docker-compose -f docker-compose.prod.yml run --rm app python manage.py maintenance_mode on || warning "Could not enable maintenance mode"
    
    # Create additional backup before migrations
    log "Creating pre-migration backup..."
    MIGRATION_BACKUP="$BACKUP_DIR/pre_migration_backup_$(date +%Y%m%d_%H%M%S).sql"
    docker exec zain-hms-db pg_dump -U postgres zain_hms > "$MIGRATION_BACKUP" || warning "Pre-migration backup failed"
    
    # Run migrations
    log "Running database migrations..."
    if docker-compose -f docker-compose.prod.yml run --rm app python manage.py migrate --verbosity=2; then
        success "Database migrations completed successfully"
        
        # Clear Django cache after migrations
        log "Clearing Django cache..."
        docker-compose -f docker-compose.prod.yml run --rm app python manage.py clear_cache || warning "Cache clearing failed"
        
        # Update search indexes if needed
        if docker-compose -f docker-compose.prod.yml run --rm app python manage.py help update_index &>/dev/null; then
            log "Updating search indexes..."
            docker-compose -f docker-compose.prod.yml run --rm app python manage.py update_index --remove --verbosity=0 || warning "Search index update failed"
        fi
        
        # Run any custom post-migration commands
        log "Running post-migration tasks..."
        docker-compose -f docker-compose.prod.yml run --rm app python manage.py post_migration_tasks || warning "Post-migration tasks had issues"
        
    else
        error "Database migration failed"
        log "Attempting to restore from backup..."
        if [ -f "$MIGRATION_BACKUP" ]; then
            docker exec -i zain-hms-db psql -U postgres -d zain_hms < "$MIGRATION_BACKUP"
            error "Migration failed. Database restored from backup."
        else
            error "Migration failed and no backup available for restoration"
        fi
    fi
    
    # Disable maintenance mode
    log "Disabling maintenance mode..."
    docker-compose -f docker-compose.prod.yml run --rm app python manage.py maintenance_mode off || warning "Could not disable maintenance mode"
    
else
    log "No pending migrations found"
fi

# Collect static files
log "Collecting static files..."
docker-compose -f docker-compose.prod.yml run --rm app python manage.py collectstatic --noinput || warning "Static files collection had issues"

# Zero-downtime deployment
log "Performing zero-downtime deployment..."

# Start new containers
docker-compose -f docker-compose.prod.yml up -d || error "Failed to start new containers"

# Health check
log "Performing health check..."
HEALTH_CHECK_URL="http://localhost:8000/health/"
for i in {1..30}; do
    if curl -f -s "$HEALTH_CHECK_URL" > /dev/null; then
        success "Health check passed"
        break
    fi
    if [ $i -eq 30 ]; then
        error "Health check failed - deployment aborted"
    fi
    log "Waiting for application to be ready... (attempt $i/30)"
    sleep 10
done

# Clean up old images
log "Cleaning up old Docker images..."
docker image prune -f

# Update version tracking
echo "$VERSION" > "$DEPLOY_DIR/.current_version"
echo "$(date): Deployed version $VERSION" >> "$DEPLOY_DIR/deployment_history.log"

# Send notification
log "Sending deployment notification..."
curl -X POST "${WEBHOOK_URL:-http://localhost:8000/api/deployment/notify/}" \
    -H "Content-Type: application/json" \
    -d '{
        "version": "'$VERSION'",
        "status": "success",
        "timestamp": "'$(date -Iseconds)'",
        "server": "'$(hostname)'"
    }' || warning "Failed to send deployment notification"

success "Deployment completed successfully!"
log "ZAIN HMS version $VERSION is now running"

# Display running containers
log "Current running containers:"
docker ps --filter name="$APP_NAME"

log "Deployment log saved to: $LOG_FILE"