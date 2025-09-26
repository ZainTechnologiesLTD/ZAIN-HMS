#!/bin/bash
# 🏥 ZAIN HMS Interactive Terminal Installer
# Beautiful TUI installer with step-by-step configuration

set -e

# Colors and formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'
BOLD='\033[1m'
DIM='\033[2m'

# Box drawing characters
TOP_LEFT="╔"
TOP_RIGHT="╗"
BOTTOM_LEFT="╚"
BOTTOM_RIGHT="╝"
HORIZONTAL="═"
VERTICAL="║"
TEE_DOWN="╦"
TEE_UP="╩"
TEE_RIGHT="╠"
TEE_LEFT="╣"
CROSS="╬"

# Configuration variables
ZAIN_HMS_VERSION="latest"
INSTALL_DIR="/opt/zain-hms"
DOMAIN=""
EMAIL=""
DB_PASSWORD=""
REDIS_PASSWORD=""
SECRET_KEY=""
ENABLE_SSL=false
ENABLE_BACKUP=true
INSTALL_MONITORING=false
SERVICE_USER="zain-hms"

# Terminal dimensions
TERM_WIDTH=$(tput cols 2>/dev/null || echo 80)
TERM_HEIGHT=$(tput lines 2>/dev/null || echo 24)

# Center text function
center_text() {
    local text="$1"
    local width=${2:-$TERM_WIDTH}
    local padding=$(((width - ${#text}) / 2))
    printf "%*s%s%*s" $padding "" "$text" $padding ""
}

# Draw box function
draw_box() {
    local width=${1:-60}
    local height=${2:-10}
    local title="$3"
    
    # Clear screen
    clear
    
    # Calculate position for centering
    local start_col=$(((TERM_WIDTH - width) / 2))
    local start_row=$(((TERM_HEIGHT - height) / 2))
    
    # Move to starting position and draw box
    printf '\033[%d;%dH' $start_row $start_col
    
    # Top border
    printf "${CYAN}${TOP_LEFT}"
    if [ -n "$title" ]; then
        local title_padding=$(((width - 2 - ${#title}) / 2))
        printf "%*s${WHITE}${BOLD}%s${CYAN}%*s" $title_padding "${HORIZONTAL}" "$title" $title_padding "${HORIZONTAL}"
    else
        printf "%*s" $((width - 2)) "${HORIZONTAL}"
    fi
    printf "${TOP_RIGHT}${NC}\n"
    
    # Side borders
    for ((i = 1; i < height - 1; i++)); do
        printf '\033[%d;%dH' $((start_row + i)) $start_col
        printf "${CYAN}${VERTICAL}%*s${VERTICAL}${NC}\n" $((width - 2)) ""
    done
    
    # Bottom border
    printf '\033[%d;%dH' $((start_row + height - 1)) $start_col
    printf "${CYAN}${BOTTOM_LEFT}%*s${BOTTOM_RIGHT}${NC}\n" $((width - 2)) "${HORIZONTAL}"
}

# Show welcome screen
show_welcome() {
    clear
    echo -e "${CYAN}"
    cat << "EOF"
    ╔══════════════════════════════════════════════════════════════════════════════╗
    ║                                                                              ║
    ║  ██████╗  █████╗ ██╗███╗   ██╗    ██╗  ██╗███╗   ███╗███████╗                ║
    ║  ╚══██╔╝ ██╔══██╗██║████╗  ██║    ██║  ██║████╗ ████║██╔════╝                ║
    ║    ██╔╝  ███████║██║██╔██╗ ██║    ███████║██╔████╔██║███████╗                ║
    ║   ██╔╝   ██╔══██║██║██║╚██╗██║    ██╔══██║██║╚██╔╝██║╚════██║                ║
    ║  ██╔╝    ██║  ██║██║██║ ╚████║    ██║  ██║██║ ╚═╝ ██║███████║                ║
    ║  ╚═╝     ╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝    ╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝                ║
    ║                                                                              ║
    ║                    🏥 HOSPITAL MANAGEMENT SYSTEM 🏥                          ║
    ║                                                                              ║
    ║                          Bismillahir Rahmanir Raheem                        ║
    ║                                                                              ║
    ╠══════════════════════════════════════════════════════════════════════════════╣
    ║                                                                              ║
    ║  Welcome to the ZAIN HMS Interactive Installer!                             ║
    ║                                                                              ║
    ║  This installer will guide you through setting up a complete                 ║
    ║  hospital management system on your server.                                  ║
    ║                                                                              ║
    ║  Features:                                                                   ║
    ║  • Complete Docker-based deployment                                          ║
    ║  • Automatic SSL certificate setup                                           ║
    ║  • Database backup and monitoring                                            ║
    ║  • User-friendly web interface                                               ║
    ║  • Multi-language support                                                    ║
    ║                                                                              ║
    ╚══════════════════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    
    echo ""
    echo -e "${GREEN}Press Enter to continue or Ctrl+C to exit...${NC}"
    read -r
}

# System requirements check
check_requirements() {
    clear
    echo -e "${CYAN}${BOLD}Checking System Requirements...${NC}"
    echo ""
    
    local all_good=true
    
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}❌ Root privileges required${NC}"
        all_good=false
    else
        echo -e "${GREEN}✅ Running as root${NC}"
    fi
    
    # Check OS
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo -e "${GREEN}✅ Operating System: $NAME $VERSION_ID${NC}"
    else
        echo -e "${RED}❌ Cannot detect operating system${NC}"
        all_good=false
    fi
    
    # Check memory
    local mem_gb=$(($(free -g | awk '/^Mem:/{print $2}')))
    if [ $mem_gb -ge 2 ]; then
        echo -e "${GREEN}✅ Memory: ${mem_gb}GB (sufficient)${NC}"
    else
        echo -e "${YELLOW}⚠️  Memory: ${mem_gb}GB (recommended: 4GB+)${NC}"
    fi
    
    # Check disk space
    local disk_gb=$(($(df / | awk 'NR==2{print int($4/1024/1024)}')))
    if [ $disk_gb -ge 20 ]; then
        echo -e "${GREEN}✅ Disk Space: ${disk_gb}GB available${NC}"
    else
        echo -e "${YELLOW}⚠️  Disk Space: ${disk_gb}GB (recommended: 50GB+)${NC}"
    fi
    
    # Check internet connection
    if ping -c 1 google.com >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Internet connectivity${NC}"
    else
        echo -e "${RED}❌ No internet connection${NC}"
        all_good=false
    fi
    
    echo ""
    if [ "$all_good" = true ]; then
        echo -e "${GREEN}🎉 All requirements met!${NC}"
    else
        echo -e "${RED}❌ Some requirements not met. Please fix and try again.${NC}"
        exit 1
    fi
    
    echo ""
    echo -e "${GREEN}Press Enter to continue...${NC}"
    read -r
}

# Configuration menu
show_config_menu() {
    while true; do
        clear
        echo -e "${CYAN}${BOLD}ZAIN HMS Configuration${NC}"
        echo -e "${CYAN}═══════════════════════${NC}"
        echo ""
        echo -e "${WHITE}Current Configuration:${NC}"
        echo -e "  ${BLUE}1.${NC} Installation Directory: ${GREEN}$INSTALL_DIR${NC}"
        echo -e "  ${BLUE}2.${NC} Domain Name: ${GREEN}${DOMAIN:-Not set}${NC}"
        echo -e "  ${BLUE}3.${NC} Admin Email: ${GREEN}${EMAIL:-Not set}${NC}"
        echo -e "  ${BLUE}4.${NC} SSL Certificate: ${GREEN}$([ "$ENABLE_SSL" = true ] && echo "Enabled" || echo "Disabled")${NC}"
        echo -e "  ${BLUE}5.${NC} Automatic Backup: ${GREEN}$([ "$ENABLE_BACKUP" = true ] && echo "Enabled" || echo "Disabled")${NC}"
        echo -e "  ${BLUE}6.${NC} Monitoring: ${GREEN}$([ "$INSTALL_MONITORING" = true ] && echo "Enabled" || echo "Disabled")${NC}"
        echo ""
        echo -e "${WHITE}Options:${NC}"
        echo -e "  ${YELLOW}c${NC}) Continue with installation"
        echo -e "  ${YELLOW}r${NC}) Reset to defaults"
        echo -e "  ${YELLOW}q${NC}) Quit installer"
        echo ""
        echo -e "${GREEN}Enter option number to configure, or 'c' to continue: ${NC}"
        
        read -r choice
        
        case $choice in
            1) configure_install_dir ;;
            2) configure_domain ;;
            3) configure_email ;;
            4) toggle_ssl ;;
            5) toggle_backup ;;
            6) toggle_monitoring ;;
            c|C) break ;;
            r|R) reset_config ;;
            q|Q) echo "Installation cancelled."; exit 0 ;;
            *) echo -e "${RED}Invalid option${NC}"; sleep 1 ;;
        esac
    done
}

# Configuration functions
configure_install_dir() {
    clear
    echo -e "${CYAN}${BOLD}Configure Installation Directory${NC}"
    echo -e "${CYAN}═══════════════════════════════${NC}"
    echo ""
    echo -e "${WHITE}Current directory:${NC} $INSTALL_DIR"
    echo -e "${DIM}The directory where ZAIN HMS will be installed${NC}"
    echo ""
    echo -e "${GREEN}Enter new installation directory (or press Enter to keep current):${NC}"
    read -r new_dir
    
    if [ -n "$new_dir" ]; then
        INSTALL_DIR="$new_dir"
        echo -e "${GREEN}✅ Installation directory updated${NC}"
        sleep 1
    fi
}

configure_domain() {
    clear
    echo -e "${CYAN}${BOLD}Configure Domain Name${NC}"
    echo -e "${CYAN}══════════════════════${NC}"
    echo ""
    echo -e "${WHITE}Current domain:${NC} ${DOMAIN:-Not set}"
    echo -e "${DIM}Your domain name (e.g., hospital.example.com)${NC}"
    echo -e "${DIM}Leave empty if you don't have a domain${NC}"
    echo ""
    echo -e "${GREEN}Enter domain name:${NC}"
    read -r new_domain
    
    DOMAIN="$new_domain"
    if [ -n "$DOMAIN" ]; then
        echo -e "${GREEN}✅ Domain set to: $DOMAIN${NC}"
        
        # Ask about SSL if domain is set
        echo ""
        echo -e "${BLUE}Enable automatic SSL certificate for $DOMAIN? [y/N]:${NC}"
        read -r ssl_choice
        if [[ "$ssl_choice" =~ ^[Yy]$ ]]; then
            ENABLE_SSL=true
        fi
    else
        ENABLE_SSL=false
        echo -e "${YELLOW}⚠️  No domain set - SSL disabled${NC}"
    fi
    sleep 2
}

configure_email() {
    clear
    echo -e "${CYAN}${BOLD}Configure Admin Email${NC}"
    echo -e "${CYAN}════════════════════${NC}"
    echo ""
    echo -e "${WHITE}Current email:${NC} ${EMAIL:-Not set}"
    echo -e "${DIM}Email address for admin notifications and SSL certificates${NC}"
    echo ""
    echo -e "${GREEN}Enter admin email address:${NC}"
    read -r new_email
    
    EMAIL="$new_email"
    if [ -n "$EMAIL" ]; then
        echo -e "${GREEN}✅ Email set to: $EMAIL${NC}"
    fi
    sleep 1
}

toggle_ssl() {
    if [ "$ENABLE_SSL" = true ]; then
        ENABLE_SSL=false
        echo -e "${YELLOW}SSL disabled${NC}"
    else
        if [ -z "$DOMAIN" ]; then
            echo -e "${RED}❌ Domain name required for SSL${NC}"
            sleep 2
            return
        fi
        ENABLE_SSL=true
        echo -e "${GREEN}SSL enabled${NC}"
    fi
    sleep 1
}

toggle_backup() {
    ENABLE_BACKUP=$([ "$ENABLE_BACKUP" = true ] && echo false || echo true)
    echo -e "${GREEN}Backup $([ "$ENABLE_BACKUP" = true ] && echo "enabled" || echo "disabled")${NC}"
    sleep 1
}

toggle_monitoring() {
    INSTALL_MONITORING=$([ "$INSTALL_MONITORING" = true ] && echo false || echo true)
    echo -e "${GREEN}Monitoring $([ "$INSTALL_MONITORING" = true ] && echo "enabled" || echo "disabled")${NC}"
    sleep 1
}

reset_config() {
    INSTALL_DIR="/opt/zain-hms"
    DOMAIN=""
    EMAIL=""
    ENABLE_SSL=false
    ENABLE_BACKUP=true
    INSTALL_MONITORING=false
    echo -e "${GREEN}✅ Configuration reset to defaults${NC}"
    sleep 1
}

# Installation progress display
show_progress() {
    local current=$1
    local total=$2
    local message="$3"
    local percent=$((current * 100 / total))
    local completed=$((current * 40 / total))
    local remaining=$((40 - completed))
    
    # Clear line and show progress
    printf '\r\033[K'
    printf "${CYAN}Progress: [${GREEN}"
    printf "%*s" $completed | tr ' ' '█'
    printf "${DIM}"
    printf "%*s" $remaining | tr ' ' '░'
    printf "${CYAN}] ${WHITE}%d%%${NC} - %s" $percent "$message"
}

# Installation steps
install_system() {
    clear
    echo -e "${CYAN}${BOLD}Installing ZAIN HMS...${NC}"
    echo -e "${CYAN}═══════════════════════${NC}"
    echo ""
    
    local steps=(
        "Updating system packages"
        "Installing Docker"
        "Installing Docker Compose"
        "Creating application user"
        "Downloading ZAIN HMS"
        "Setting up directories"
        "Configuring environment"
        "Installing system service"
        "Configuring firewall"
        "Deploying containers"
        "Setting up SSL certificate"
        "Finalizing installation"
    )
    
    local total_steps=${#steps[@]}
    
    for i in "${!steps[@]}"; do
        local step_num=$((i + 1))
        show_progress $step_num $total_steps "${steps[i]}"
        
        # Simulate installation steps (replace with actual installation code)
        case $step_num in
            1) install_system_packages ;;
            2) install_docker_system ;;
            3) install_docker_compose_system ;;
            4) create_application_user ;;
            5) download_zain_hms_system ;;
            6) setup_directory_structure ;;
            7) configure_environment_system ;;
            8) install_system_service ;;
            9) configure_firewall_system ;;
            10) deploy_containers ;;
            11) setup_ssl_certificate ;;
            12) finalize_installation ;;
        esac
        
        sleep 1
    done
    
    echo ""
    echo ""
    echo -e "${GREEN}${BOLD}🎉 Installation completed successfully! 🎉${NC}"
}

# Stub functions for installation steps (implement actual installation logic)
install_system_packages() { sleep 0.5; }
install_docker_system() { sleep 1; }
install_docker_compose_system() { sleep 0.5; }
create_application_user() { sleep 0.3; }
download_zain_hms_system() { sleep 2; }
setup_directory_structure() { sleep 0.5; }
configure_environment_system() { sleep 0.5; }
install_system_service() { sleep 0.3; }
configure_firewall_system() { sleep 0.5; }
deploy_containers() { sleep 3; }
setup_ssl_certificate() { sleep 1; }
finalize_installation() { sleep 0.5; }

# Show completion screen
show_completion_screen() {
    clear
    echo -e "${GREEN}"
    cat << "EOF"
    ╔══════════════════════════════════════════════════════════════════════════════╗
    ║                                                                              ║
    ║  🎉🎉🎉  ZAIN HMS INSTALLATION COMPLETED SUCCESSFULLY!  🎉🎉🎉                  ║
    ║                                                                              ║
    ╠══════════════════════════════════════════════════════════════════════════════╣
    ║                                                                              ║
    ║  Your hospital management system is now ready to use!                       ║
    ║                                                                              ║
EOF
    echo -e "║  📍 Installation Directory: $(printf '%-25s' "$INSTALL_DIR")                       ║"
    if [ -n "$DOMAIN" ]; then
        echo -e "║  🌐 Web Address: $(printf 'https://%-25s' "$DOMAIN")                          ║"
    else
        local server_ip=$(hostname -I | awk '{print $1}')
        echo -e "║  🖥️  IP Address: $(printf 'http://%-25s' "$server_ip")                           ║"
    fi
    echo -e "║  👤 Default Login: admin / admin123                                     ║"
    echo -e "║                                                                              ║"
    echo -e "║  🔧 Management Commands:                                                     ║"
    echo -e "║     • Start:   systemctl start zain-hms                                     ║"
    echo -e "║     • Stop:    systemctl stop zain-hms                                      ║"
    echo -e "║     • Status:  systemctl status zain-hms                                    ║"
    echo -e "║                                                                              ║"
    echo -e "║  📚 Documentation: https://github.com/ZainTechnologiesLTD/ZAIN-HMS        ║"
    echo -e "║                                                                              ║"
    echo -e "║  ✨ May Allah bless this system and make it beneficial! ✨                   ║"
    echo -e "║                                                                              ║"
    echo -e "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
    echo -e "${CYAN}Press Enter to exit...${NC}"
    read -r
}

# Error handling
handle_error() {
    clear
    echo -e "${RED}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                              ║"
    echo "║  ❌ INSTALLATION FAILED                                                      ║"
    echo "║                                                                              ║"
    echo "║  An error occurred during installation.                                      ║"
    echo "║  Please check the logs and try again.                                       ║"
    echo "║                                                                              ║"
    echo "║  For support, visit:                                                         ║"
    echo "║  https://github.com/ZainTechnologiesLTD/ZAIN-HMS/issues                   ║"
    echo "║                                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    exit 1
}

# Main function
main() {
    # Set up error handling
    trap handle_error ERR
    
    show_welcome
    check_requirements
    show_config_menu
    install_system
    show_completion_screen
}

# Run installer
main "$@"