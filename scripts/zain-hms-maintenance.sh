#!/bin/bash
# 🏥 ZAIN HMS Maintenance and Update Tools
# Comprehensive maintenance utilities for ZAIN HMS installation

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Configuration
INSTALL_DIR="/opt/zain-hms"
SERVICE_USER="zain-hms"
BACKUP_DIR="/var/backups/zain-hms"
LOG_FILE="/var/log/zain-hms-maintenance.log"

# Function to log actions
log_action() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Function to show header
show_header() {
    clear
    echo -e "${CYAN}╔══════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                                                      ║${NC}"
    echo -e "${CYAN}║              🏥 ZAIN HMS Maintenance                 ║${NC}"
    echo -e "${CYAN}║           Hospital Management System                 ║${NC}"
    echo -e "${CYAN}║                                                      ║${NC}"
    echo -e "${CYAN}║              Bismillahir Rahmanir Raheem             ║${NC}"
    echo -e "${CYAN}║                                                      ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Function to show main menu
show_menu() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}                   🔧 MAINTENANCE MENU               ${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${YELLOW}System Management:${NC}"
    echo "  1) 🔄 Update ZAIN HMS"
    echo "  2) 🔄 Restart Services"
    echo "  3) ⏹️  Stop Services"
    echo "  4) ▶️  Start Services"
    echo "  5) 📊 System Status"
    echo ""
    echo -e "${YELLOW}Backup & Restore:${NC}"
    echo "  6) 💾 Create Backup"
    echo "  7) 📤 Restore Backup"
    echo "  8) 🗂️  List Backups"
    echo "  9) 🗑️  Clean Old Backups"
    echo ""
    echo -e "${YELLOW}Database Operations:${NC}"
    echo "  10) 🔧 Database Maintenance"
    echo "  11) 📊 Database Status"
    echo "  12) 🔒 Change Database Password"
    echo ""
    echo -e "${YELLOW}Security & Monitoring:${NC}"
    echo "  13) 🔒 Security Audit"
    echo "  14) 📈 Performance Monitor"
    echo "  15) 🔍 View Logs"
    echo "  16) 🧹 Clean Logs"
    echo ""
    echo -e "${YELLOW}Configuration:${NC}"
    echo "  17) ⚙️  Update Configuration"
    echo "  18) 🌐 Setup SSL Certificate"
    echo "  19) 🔥 Configure Firewall"
    echo ""
    echo -e "${YELLOW}Troubleshooting:${NC}"
    echo "  20) 🩺 Health Check"
    echo "  21) 🔧 Reset to Defaults"
    echo "  22) 🗑️  Complete Uninstall"
    echo ""
    echo -e "${YELLOW}Other:${NC}"
    echo "  23) ℹ️  System Information"
    echo "  24) 📖 View Documentation"
    echo "  0) ❌ Exit"
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
}

# Function to check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}❌ This script must be run as root${NC}"
        echo "Please run: sudo $0"
        exit 1
    fi
}

# Function to check if ZAIN HMS is installed
check_installation() {
    if [ ! -d "$INSTALL_DIR" ]; then
        echo -e "${RED}❌ ZAIN HMS installation not found at $INSTALL_DIR${NC}"
        echo "Please install ZAIN HMS first."
        exit 1
    fi
}

# 1. Update ZAIN HMS
update_system() {
    echo -e "${YELLOW}🔄 Updating ZAIN HMS...${NC}"
    log_action "Starting system update"
    
    cd "$INSTALL_DIR"
    
    # Create backup before update
    echo -e "${BLUE}Creating pre-update backup...${NC}"
    create_backup "pre-update-$(date +%Y%m%d-%H%M%S)"
    
    # Pull latest images
    echo -e "${BLUE}Updating Docker images...${NC}"
    sudo -u "$SERVICE_USER" docker-compose -f docker-compose.prod.yml pull
    
    # Restart with new images
    echo -e "${BLUE}Restarting services with updates...${NC}"
    sudo -u "$SERVICE_USER" docker-compose -f docker-compose.prod.yml up -d
    
    # Run migrations if needed
    echo -e "${BLUE}Running database migrations...${NC}"
    sudo -u "$SERVICE_USER" docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
    
    echo -e "${GREEN}✅ System updated successfully${NC}"
    log_action "System update completed"
    
    read -p "Press Enter to continue..."
}

# 2-4. Service Management Functions
restart_services() {
    echo -e "${YELLOW}🔄 Restarting ZAIN HMS services...${NC}"
    log_action "Restarting services"
    
    cd "$INSTALL_DIR"
    sudo -u "$SERVICE_USER" docker-compose -f docker-compose.prod.yml restart
    
    echo -e "${GREEN}✅ Services restarted${NC}"
    log_action "Services restart completed"
    
    read -p "Press Enter to continue..."
}

stop_services() {
    echo -e "${YELLOW}⏹️ Stopping ZAIN HMS services...${NC}"
    log_action "Stopping services"
    
    cd "$INSTALL_DIR"
    sudo -u "$SERVICE_USER" docker-compose -f docker-compose.prod.yml down
    
    echo -e "${GREEN}✅ Services stopped${NC}"
    log_action "Services stopped"
    
    read -p "Press Enter to continue..."
}

start_services() {
    echo -e "${YELLOW}▶️ Starting ZAIN HMS services...${NC}"
    log_action "Starting services"
    
    cd "$INSTALL_DIR"
    sudo -u "$SERVICE_USER" docker-compose -f docker-compose.prod.yml up -d
    
    echo -e "${GREEN}✅ Services started${NC}"
    log_action "Services started"
    
    read -p "Press Enter to continue..."
}

# 5. System Status
show_status() {
    echo -e "${YELLOW}📊 ZAIN HMS System Status${NC}"
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    
    cd "$INSTALL_DIR"
    
    # Docker services status
    echo -e "${CYAN}Docker Services:${NC}"
    sudo -u "$SERVICE_USER" docker-compose -f docker-compose.prod.yml ps
    
    echo ""
    echo -e "${CYAN}System Resources:${NC}"
    echo "Memory Usage:"
    free -h
    
    echo ""
    echo "Disk Usage:"
    df -h "$INSTALL_DIR"
    
    echo ""
    echo -e "${CYAN}Service Health:${NC}"
    if curl -f http://localhost/health/ >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Web Application: Healthy${NC}"
    else
        echo -e "${RED}❌ Web Application: Not responding${NC}"
    fi
    
    echo ""
    read -p "Press Enter to continue..."
}

# 6. Create Backup
create_backup() {
    local backup_name="${1:-backup-$(date +%Y%m%d-%H%M%S)}"
    echo -e "${YELLOW}💾 Creating backup: $backup_name${NC}"
    log_action "Creating backup: $backup_name"
    
    mkdir -p "$BACKUP_DIR"
    local backup_path="$BACKUP_DIR/$backup_name"
    mkdir -p "$backup_path"
    
    cd "$INSTALL_DIR"
    
    # Backup database
    echo -e "${BLUE}Backing up database...${NC}"
    sudo -u "$SERVICE_USER" docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U zain_hms zain_hms > "$backup_path/database.sql"
    
    # Backup media files
    echo -e "${BLUE}Backing up media files...${NC}"
    tar -czf "$backup_path/media.tar.gz" -C "$INSTALL_DIR" data/media
    
    # Backup configuration
    echo -e "${BLUE}Backing up configuration...${NC}"
    cp .env.prod "$backup_path/"
    cp docker-compose.prod.yml "$backup_path/"
    
    # Create backup info
    cat > "$backup_path/backup_info.txt" << EOF
ZAIN HMS Backup Information
==========================
Backup Date: $(date)
Backup Name: $backup_name
Database: Included
Media Files: Included
Configuration: Included
EOF
    
    echo -e "${GREEN}✅ Backup created: $backup_path${NC}"
    log_action "Backup completed: $backup_path"
    
    if [ -z "${1:-}" ]; then
        read -p "Press Enter to continue..."
    fi
}

# 7. Restore Backup
restore_backup() {
    echo -e "${YELLOW}📤 Available backups:${NC}"
    ls -la "$BACKUP_DIR"
    
    echo ""
    read -p "Enter backup name to restore: " backup_name
    
    local backup_path="$BACKUP_DIR/$backup_name"
    
    if [ ! -d "$backup_path" ]; then
        echo -e "${RED}❌ Backup not found: $backup_path${NC}"
        read -p "Press Enter to continue..."
        return
    fi
    
    echo -e "${RED}⚠️  WARNING: This will overwrite current data!${NC}"
    read -p "Are you sure you want to restore? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        echo "Restore cancelled."
        return
    fi
    
    echo -e "${YELLOW}📤 Restoring backup: $backup_name${NC}"
    log_action "Restoring backup: $backup_name"
    
    cd "$INSTALL_DIR"
    
    # Stop services
    sudo -u "$SERVICE_USER" docker-compose -f docker-compose.prod.yml down
    
    # Restore database
    if [ -f "$backup_path/database.sql" ]; then
        echo -e "${BLUE}Restoring database...${NC}"
        sudo -u "$SERVICE_USER" docker-compose -f docker-compose.prod.yml up -d db
        sleep 10
        cat "$backup_path/database.sql" | sudo -u "$SERVICE_USER" docker-compose -f docker-compose.prod.yml exec -T db psql -U zain_hms -d zain_hms
    fi
    
    # Restore media files
    if [ -f "$backup_path/media.tar.gz" ]; then
        echo -e "${BLUE}Restoring media files...${NC}"
        tar -xzf "$backup_path/media.tar.gz" -C "$INSTALL_DIR"
    fi
    
    # Restore configuration
    if [ -f "$backup_path/.env.prod" ]; then
        echo -e "${BLUE}Restoring configuration...${NC}"
        cp "$backup_path/.env.prod" .env.prod
    fi
    
    # Start services
    sudo -u "$SERVICE_USER" docker-compose -f docker-compose.prod.yml up -d
    
    echo -e "${GREEN}✅ Backup restored successfully${NC}"
    log_action "Backup restore completed"
    
    read -p "Press Enter to continue..."
}

# 8. List Backups
list_backups() {
    echo -e "${YELLOW}🗂️ Available backups:${NC}"
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    
    if [ -d "$BACKUP_DIR" ]; then
        for backup in "$BACKUP_DIR"/*; do
            if [ -d "$backup" ]; then
                local backup_name=$(basename "$backup")
                local backup_size=$(du -sh "$backup" | cut -f1)
                local backup_date=""
                
                if [ -f "$backup/backup_info.txt" ]; then
                    backup_date=$(grep "Backup Date:" "$backup/backup_info.txt" | cut -d: -f2- | xargs)
                fi
                
                echo -e "${GREEN}📦 $backup_name${NC} (${backup_size})"
                if [ -n "$backup_date" ]; then
                    echo -e "   📅 $backup_date"
                fi
                echo ""
            fi
        done
    else
        echo "No backups found."
    fi
    
    read -p "Press Enter to continue..."
}

# 9. Clean Old Backups
clean_old_backups() {
    echo -e "${YELLOW}🗑️ Cleaning old backups...${NC}"
    
    read -p "Keep how many recent backups? (default: 5): " keep_count
    keep_count=${keep_count:-5}
    
    if [ -d "$BACKUP_DIR" ]; then
        local backup_count=$(ls -1 "$BACKUP_DIR" | wc -l)
        
        if [ "$backup_count" -gt "$keep_count" ]; then
            echo -e "${BLUE}Found $backup_count backups, keeping $keep_count most recent...${NC}"
            
            # Remove old backups
            ls -1t "$BACKUP_DIR" | tail -n +$((keep_count + 1)) | while read old_backup; do
                echo -e "${RED}Removing: $old_backup${NC}"
                rm -rf "$BACKUP_DIR/$old_backup"
            done
            
            echo -e "${GREEN}✅ Old backups cleaned${NC}"
        else
            echo -e "${GREEN}✅ No old backups to clean${NC}"
        fi
    fi
    
    log_action "Old backups cleaned, keeping $keep_count"
    
    read -p "Press Enter to continue..."
}

# 20. Health Check
health_check() {
    echo -e "${YELLOW}🩺 ZAIN HMS Health Check${NC}"
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    
    local issues=0
    
    # Check Docker
    if command -v docker >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Docker: Installed${NC}"
    else
        echo -e "${RED}❌ Docker: Not installed${NC}"
        ((issues++))
    fi
    
    # Check Docker Compose
    if command -v docker-compose >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Docker Compose: Installed${NC}"
    else
        echo -e "${RED}❌ Docker Compose: Not installed${NC}"
        ((issues++))
    fi
    
    # Check installation directory
    if [ -d "$INSTALL_DIR" ]; then
        echo -e "${GREEN}✅ Installation Directory: Present${NC}"
    else
        echo -e "${RED}❌ Installation Directory: Missing${NC}"
        ((issues++))
    fi
    
    # Check services
    cd "$INSTALL_DIR"
    if sudo -u "$SERVICE_USER" docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
        echo -e "${GREEN}✅ Docker Services: Running${NC}"
    else
        echo -e "${RED}❌ Docker Services: Not running${NC}"
        ((issues++))
    fi
    
    # Check web application
    if curl -f http://localhost/health/ >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Web Application: Responding${NC}"
    else
        echo -e "${RED}❌ Web Application: Not responding${NC}"
        ((issues++))
    fi
    
    # Check disk space
    local disk_usage=$(df "$INSTALL_DIR" | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$disk_usage" -lt 80 ]; then
        echo -e "${GREEN}✅ Disk Space: $disk_usage% used${NC}"
    else
        echo -e "${YELLOW}⚠️  Disk Space: $disk_usage% used (Warning)${NC}"
    fi
    
    # Check memory
    local mem_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    if [ "$mem_usage" -lt 80 ]; then
        echo -e "${GREEN}✅ Memory Usage: $mem_usage%${NC}"
    else
        echo -e "${YELLOW}⚠️  Memory Usage: $mem_usage% (High)${NC}"
    fi
    
    echo ""
    if [ "$issues" -eq 0 ]; then
        echo -e "${GREEN}🎉 All checks passed! System is healthy.${NC}"
    else
        echo -e "${RED}⚠️  Found $issues issues. Please review and fix.${NC}"
    fi
    
    read -p "Press Enter to continue..."
}

# 22. Complete Uninstall
complete_uninstall() {
    echo -e "${RED}🗑️ COMPLETE UNINSTALL${NC}"
    echo -e "${RED}═══════════════════════════════════════${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  WARNING: This will completely remove ZAIN HMS!${NC}"
    echo "This action will:"
    echo "• Stop all services"
    echo "• Remove Docker containers and images"
    echo "• Delete all data and configuration"
    echo "• Remove systemd service"
    echo "• Delete installation directory"
    echo ""
    
    read -p "Type 'DELETE EVERYTHING' to confirm: " confirm
    
    if [ "$confirm" != "DELETE EVERYTHING" ]; then
        echo "Uninstall cancelled."
        return
    fi
    
    echo -e "${RED}🗑️ Uninstalling ZAIN HMS...${NC}"
    log_action "Starting complete uninstall"
    
    # Stop systemd service
    systemctl stop zain-hms 2>/dev/null || true
    systemctl disable zain-hms 2>/dev/null || true
    rm -f /etc/systemd/system/zain-hms.service
    systemctl daemon-reload
    
    # Stop and remove Docker containers
    if [ -d "$INSTALL_DIR" ]; then
        cd "$INSTALL_DIR"
        sudo -u "$SERVICE_USER" docker-compose -f docker-compose.prod.yml down -v --rmi all 2>/dev/null || true
    fi
    
    # Remove installation directory
    rm -rf "$INSTALL_DIR"
    
    # Remove user
    userdel -r "$SERVICE_USER" 2>/dev/null || true
    
    # Remove backups (optional)
    read -p "Remove all backups too? (y/n): " remove_backups
    if [ "$remove_backups" = "y" ] || [ "$remove_backups" = "Y" ]; then
        rm -rf "$BACKUP_DIR"
    fi
    
    echo -e "${GREEN}✅ ZAIN HMS completely uninstalled${NC}"
    log_action "Complete uninstall finished"
    
    read -p "Press Enter to exit..."
    exit 0
}

# Main menu loop
main_menu() {
    while true; do
        show_header
        show_menu
        
        read -p "Enter your choice (0-24): " choice
        
        case $choice in
            1) update_system ;;
            2) restart_services ;;
            3) stop_services ;;
            4) start_services ;;
            5) show_status ;;
            6) create_backup ;;
            7) restore_backup ;;
            8) list_backups ;;
            9) clean_old_backups ;;
            20) health_check ;;
            22) complete_uninstall ;;
            23) 
                echo -e "${CYAN}System Information:${NC}"
                echo "Installation Directory: $INSTALL_DIR"
                echo "Service User: $SERVICE_USER"
                echo "Backup Directory: $BACKUP_DIR"
                echo "Log File: $LOG_FILE"
                uname -a
                read -p "Press Enter to continue..."
                ;;
            0) 
                echo -e "${GREEN}May Allah bless your work! Goodbye! 👋${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}❌ Invalid option. Please try again.${NC}"
                read -p "Press Enter to continue..."
                ;;
        esac
    done
}

# Initialize
check_root
check_installation

# Create log directory
mkdir -p "$(dirname "$LOG_FILE")"
touch "$LOG_FILE"

# Start main menu
main_menu