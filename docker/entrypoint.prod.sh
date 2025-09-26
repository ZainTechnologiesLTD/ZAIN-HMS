#!/bin/bash
# 🏥 ZAIN HMS Production Entry Point Script
# Handles initialization and startup for production container

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🏥 ZAIN HMS Production Container Startup${NC}"
echo "==========================================="

# Function to wait for database
wait_for_db() {
    echo -e "${YELLOW}⏳ Waiting for PostgreSQL database...${NC}"
    
    until PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c '\q' > /dev/null 2>&1; do
        echo -e "${YELLOW}Database is unavailable - sleeping${NC}"
        sleep 2
    done
    
    echo -e "${GREEN}✅ Database is ready!${NC}"
}

# Function to wait for Redis
wait_for_redis() {
    echo -e "${YELLOW}⏳ Waiting for Redis cache...${NC}"
    
    until redis-cli -h redis ping > /dev/null 2>&1; do
        echo -e "${YELLOW}Redis is unavailable - sleeping${NC}"
        sleep 2
    done
    
    echo -e "${GREEN}✅ Redis is ready!${NC}"
}

# Extract database connection details from DATABASE_URL if set
if [ -n "$DATABASE_URL" ]; then
    # Parse DATABASE_URL: postgresql://user:password@host:port/dbname
    DB_HOST=$(echo $DATABASE_URL | sed 's|.*@\([^:]*\).*|\1|')
    DB_USER=$(echo $DATABASE_URL | sed 's|.*://\([^:]*\):.*|\1|')
    DB_PASSWORD=$(echo $DATABASE_URL | sed 's|.*://[^:]*:\([^@]*\)@.*|\1|')
    DB_NAME=$(echo $DATABASE_URL | sed 's|.*/\([^?]*\).*|\1|')
fi

# Set defaults if not provided
DB_HOST=${DB_HOST:-db}
DB_USER=${DB_USER:-zain_hms_user}
DB_NAME=${DB_NAME:-zain_hms}

# Wait for services
wait_for_db
wait_for_redis

echo -e "${BLUE}🔧 Running Django setup commands...${NC}"

# Run migrations
echo -e "${YELLOW}📊 Running database migrations...${NC}"
python manage.py migrate --noinput
echo -e "${GREEN}✅ Migrations completed${NC}"

# Create superuser if it doesn't exist
echo -e "${YELLOW}👤 Creating superuser (if needed)...${NC}"
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@zainhms.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
" || true

# Collect static files (already done in Docker build, but just in case)
echo -e "${YELLOW}📦 Collecting static files...${NC}"
python manage.py collectstatic --noinput --clear
echo -e "${GREEN}✅ Static files collected${NC}"

# Compile messages (if translations are used)
echo -e "${YELLOW}🌐 Compiling translation messages...${NC}"
python manage.py compilemessages || true
echo -e "${GREEN}✅ Messages compiled${NC}"

# Clear cache
echo -e "${YELLOW}🧹 Clearing cache...${NC}"
python manage.py shell -c "
from django.core.cache import cache
cache.clear()
print('Cache cleared')
" || true

# Set proper permissions
echo -e "${YELLOW}🔒 Setting file permissions...${NC}"
chmod -R 755 /app/staticfiles || true
chmod -R 755 /app/media || true
chmod -R 755 /app/logs || true

echo -e "${GREEN}✅ All setup commands completed successfully!${NC}"
echo -e "${BLUE}🚀 Starting application...${NC}"

# Execute the main command
exec "$@"