/**
 * Clean Sidebar JavaScript
 * Modern vanilla JavaScript approach with no conflicts
 * Handles sidebar toggle, dropdowns, and responsive behavior
 */

class SidebarManager {
    constructor() {
        this.sidebar = null;
        this.sidebarToggle = null;
        this.isCollapsed = false;
        this.isMobile = window.innerWidth <= 768;
        this.isActive = false;

        // Initialize when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    init() {
        this.sidebar = document.getElementById('sidebar');
        this.sidebarToggle = document.querySelector('.sidebar-toggle');

        if (!this.sidebar) {
            console.warn('Sidebar element not found');
            return;
        }

        this.setupEventListeners();
        this.handleResponsive();
        this.initializeDropdowns();
        this.setActiveMenuItem();

        // Load saved state
        this.loadSidebarState();

        console.log('Clean Sidebar initialized successfully');
    }

    setupEventListeners() {
        // Sidebar toggle
        if (this.sidebarToggle) {
            this.sidebarToggle.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleSidebar();
            });
        }

        // Close sidebar on mobile when clicking outside
        document.addEventListener('click', (e) => {
            if (this.isMobile && this.isActive) {
                if (!this.sidebar.contains(e.target) && !e.target.closest('.sidebar-toggle')) {
                    this.closeMobileSidebar();
                }
            }
        });

        // Handle window resize
        window.addEventListener('resize', () => {
            this.handleResize();
        });

        // Handle escape key on mobile
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isMobile && this.isActive) {
                this.closeMobileSidebar();
            }
        });
    }

    toggleSidebar() {
        if (this.isMobile) {
            this.toggleMobileSidebar();
        } else {
            this.toggleDesktopSidebar();
        }
    }

    toggleDesktopSidebar() {
        this.isCollapsed = !this.isCollapsed;

        if (this.isCollapsed) {
            this.sidebar.classList.add('collapsed');
        } else {
            this.sidebar.classList.remove('collapsed');
        }

        // Save state
        localStorage.setItem('sidebarCollapsed', this.isCollapsed.toString());

        // Trigger custom event for other components
        window.dispatchEvent(new CustomEvent('sidebarToggle', {
            detail: { collapsed: this.isCollapsed }
        }));
    }

    toggleMobileSidebar() {
        this.isActive = !this.isActive;

        if (this.isActive) {
            this.sidebar.classList.add('active');
            document.body.style.overflow = 'hidden'; // Prevent background scroll
        } else {
            this.sidebar.classList.remove('active');
            document.body.style.overflow = '';
        }
    }

    closeMobileSidebar() {
        this.isActive = false;
        this.sidebar.classList.remove('active');
        document.body.style.overflow = '';
    }

    handleResize() {
        const wasMobile = this.isMobile;
        this.isMobile = window.innerWidth <= 768;

        // Transitioning from mobile to desktop
        if (wasMobile && !this.isMobile) {
            this.sidebar.classList.remove('active');
            document.body.style.overflow = '';
            this.isActive = false;
        }

        // Transitioning from desktop to mobile
        if (!wasMobile && this.isMobile) {
            this.sidebar.classList.remove('collapsed');
        }
    }

    handleResponsive() {
        this.isMobile = window.innerWidth <= 768;

        if (this.isMobile) {
            this.sidebar.classList.remove('collapsed');
        }
    }

    initializeDropdowns() {
        const dropdownToggles = document.querySelectorAll('[data-dropdown-toggle]');

        dropdownToggles.forEach(toggle => {
            const dropdown = toggle.closest('.nav-dropdown');

            toggle.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleDropdown(dropdown);
            });
        });
    }

    toggleDropdown(dropdown) {
        const isOpen = dropdown.classList.contains('show');

        // Close all other dropdowns
        document.querySelectorAll('.nav-dropdown.show').forEach(openDropdown => {
            if (openDropdown !== dropdown) {
                openDropdown.classList.remove('show');
            }
        });

        // Toggle current dropdown
        if (isOpen) {
            dropdown.classList.remove('show');
        } else {
            dropdown.classList.add('show');
        }
    }

    setActiveMenuItem() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.sidebar-nav a');

        navLinks.forEach(link => {
            link.classList.remove('active');

            const href = link.getAttribute('href');
            if (href && currentPath.includes(href) && href !== '/') {
                link.classList.add('active');

                // If it's in a dropdown, open the dropdown
                const dropdown = link.closest('.nav-dropdown');
                if (dropdown) {
                    dropdown.classList.add('show');
                }
            }
        });
    }

    loadSidebarState() {
        if (!this.isMobile) {
            const savedState = localStorage.getItem('sidebarCollapsed');
            if (savedState === 'true') {
                this.isCollapsed = true;
                this.sidebar.classList.add('collapsed');
            }
        }
    }

    // Public API methods
    collapse() {
        if (!this.isMobile) {
            this.isCollapsed = true;
            this.sidebar.classList.add('collapsed');
            localStorage.setItem('sidebarCollapsed', 'true');
        }
    }

    expand() {
        if (!this.isMobile) {
            this.isCollapsed = false;
            this.sidebar.classList.remove('collapsed');
            localStorage.setItem('sidebarCollapsed', 'false');
        }
    }

    isCollapsedState() {
        return this.isCollapsed;
    }

    isMobileState() {
        return this.isMobile;
    }
}

// Initialize sidebar when script loads
const sidebar = new SidebarManager();

// Export for potential use in other scripts
if (typeof window !== 'undefined') {
    window.SidebarManager = sidebar;
}

// Alternative initialization for HTMX compatibility
document.addEventListener('htmx:afterSwap', () => {
    // Re-initialize dropdowns and active states after HTMX content swap
    if (window.SidebarManager) {
        window.SidebarManager.initializeDropdowns();
        window.SidebarManager.setActiveMenuItem();
    }
});

// Additional Alpine.js compatibility if needed
document.addEventListener('alpine:init', () => {
    if (typeof Alpine !== 'undefined') {
        Alpine.data('sidebar', () => ({
            collapsed: false,
            mobile: window.innerWidth <= 768,

            init() {
                this.collapsed = localStorage.getItem('sidebarCollapsed') === 'true';
                this.$watch('collapsed', value => {
                    localStorage.setItem('sidebarCollapsed', value.toString());
                });
            },

            toggle() {
                if (window.SidebarManager) {
                    window.SidebarManager.toggleSidebar();
                    this.collapsed = window.SidebarManager.isCollapsedState();
                }
            }
        }));
    }
});
