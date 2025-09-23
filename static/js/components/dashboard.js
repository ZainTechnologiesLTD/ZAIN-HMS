/**
 * Dashboard Component JavaScript
 * Centralized JavaScript for all dashboard functionality
 */

// DashboardComponents namespace (avoid conflict with Dashboard class)
const DashboardComponents = {
    
    // Initialize all dashboard features
    init() {
        this.initSidebar();
        this.initSearch();
        this.initNotifications();
        this.initTooltips();
        this.initModals();
        this.initTables();
        this.initCharts();
        this.initScrollToTop();
        this.initThemeToggle();
        this.initLanguageSwitcher();
    },

    // Sidebar functionality
    initSidebar() {
        // Our templates render the sidebar with class 'sidebar'
        const sidebar = document.querySelector('.sidebar');
        const toggle = document.getElementById('sidebarToggle');
        const overlay = document.getElementById('sidebarOverlay');
        const body = document.body;

        if (toggle && sidebar) {
            toggle.addEventListener('click', () => {
                if (window.innerWidth < 768) {
                    // Mobile: slide in/out
                    sidebar.classList.toggle('show');
                    overlay?.classList.toggle('show');
                    body.classList.toggle('sidebar-open');
                } else {
                    // Desktop: collapse/expand width
                    sidebar.classList.toggle('collapsed');
                }
            });
        }

        if (overlay) {
            overlay.addEventListener('click', () => {
                sidebar?.classList.remove('show');
                overlay.classList.remove('show');
                body.classList.remove('sidebar-open');
            });
        }

        // Handle responsive sidebar
        this.handleResponsiveSidebar();
        window.addEventListener('resize', () => this.handleResponsiveSidebar());
        
        // Initialize dropdown functionality for sidebar submenus
        this.initSidebarDropdowns();
    },
    
    // Initialize sidebar dropdown functionality
    initSidebarDropdowns() {
        const dropdownToggles = document.querySelectorAll('[data-dropdown-toggle]');
        
        dropdownToggles.forEach(toggle => {
            const dropdown = toggle.closest('.nav-dropdown');
            
            if (dropdown) {
                toggle.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.toggleSidebarDropdown(dropdown);
                });
            }
        });
    },
    
    // Toggle sidebar dropdown
    toggleSidebarDropdown(dropdown) {
        const isOpen = dropdown.classList.contains('show');
        
        // Close all other dropdowns first
        document.querySelectorAll('.nav-dropdown.show').forEach(openDropdown => {
            if (openDropdown !== dropdown) {
                openDropdown.classList.remove('show');
            }
        });
        
        // Toggle current dropdown
        dropdown.classList.toggle('show', !isOpen);
    },

    // Handle responsive sidebar behavior
    handleResponsiveSidebar() {
    const sidebar = document.querySelector('.sidebar');
        const body = document.body;
        const overlay = document.getElementById('sidebarOverlay');
        
        if (window.innerWidth >= 768) {
            sidebar?.classList.remove('show');
            overlay?.classList.remove('show');
            body.classList.remove('sidebar-open');
        }
    },

    // Initialize search functionality
    initSearch() {
        const searchInput = document.getElementById('globalSearch');
        const searchResults = document.getElementById('searchResults');
        const searchLoading = document.getElementById('searchLoading');
        const searchContent = document.getElementById('searchContent');
        const searchEmpty = document.getElementById('searchEmpty');
        let searchTimeout;

        if (searchInput && searchResults) {
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                const query = e.target.value.trim();
                
                if (query.length > 2) {
                    // Show loading state
                    this.showSearchResults();
                    this.showSearchLoading();
                    
                    searchTimeout = setTimeout(() => {
                        this.performSearch(query);
                    }, 300);
                } else {
                    this.hideSearchResults();
                }
            });

            // Hide search results when clicking outside
            document.addEventListener('click', (e) => {
                if (!searchInput.closest('.search-box').contains(e.target)) {
                    this.hideSearchResults();
                }
            });

            // Show search results when input is focused and has content
            searchInput.addEventListener('focus', (e) => {
                const query = e.target.value.trim();
                if (query.length > 2) {
                    this.showSearchResults();
                }
            });
        }
    },

    // Show search results dropdown
    showSearchResults() {
        const searchResults = document.getElementById('searchResults');
        if (searchResults) {
            searchResults.classList.add('show');
        }
    },

    // Hide search results dropdown
    hideSearchResults() {
        const searchResults = document.getElementById('searchResults');
        if (searchResults) {
            searchResults.classList.remove('show');
        }
    },

    // Show search loading state
    showSearchLoading() {
        const searchLoading = document.getElementById('searchLoading');
        const searchContent = document.getElementById('searchContent');
        const searchEmpty = document.getElementById('searchEmpty');
        
        if (searchLoading) searchLoading.classList.add('show');
        if (searchContent) searchContent.style.display = 'none';
        if (searchEmpty) searchEmpty.classList.remove('show');
    },

    // Show search content
    showSearchContent() {
        const searchLoading = document.getElementById('searchLoading');
        const searchContent = document.getElementById('searchContent');
        const searchEmpty = document.getElementById('searchEmpty');
        
        if (searchLoading) searchLoading.classList.remove('show');
        if (searchContent) searchContent.style.display = 'block';
        if (searchEmpty) searchEmpty.classList.remove('show');
    },

    // Show search empty state
    showSearchEmpty() {
        const searchLoading = document.getElementById('searchLoading');
        const searchContent = document.getElementById('searchContent');
        const searchEmpty = document.getElementById('searchEmpty');
        
        if (searchLoading) searchLoading.classList.remove('show');
        if (searchContent) searchContent.style.display = 'none';
        if (searchEmpty) searchEmpty.classList.add('show');
    },

    // Perform global search
    performSearch(query) {
        console.log('Searching for:', query);
        
        // Make AJAX request to search endpoint
        fetch(`/en/dashboard/search/?q=${encodeURIComponent(query)}`, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': document.querySelector('meta[name=csrf-token]')?.content || ''
            }
        })
        .then(response => response.json())
        .then(data => {
            this.displaySearchResults(data);
        })
        .catch(error => {
            console.error('Search error:', error);
            this.showSearchEmpty();
        });
    },

    // Display search results
    displaySearchResults(data) {
        const searchContent = document.getElementById('searchContent');
        
        if (!searchContent) return;
        
        if (data.results && data.results.length > 0) {
            let html = '';
            
            data.results.forEach(result => {
                html += `
                    <div class="search-item" onclick="window.location.href='${result.url}'">
                        <div class="search-item-category">${result.category}</div>
                        <div class="search-item-title">${result.title}</div>
                        <div class="search-item-description">${result.description}</div>
                    </div>
                `;
            });
            
            searchContent.innerHTML = html;
            this.showSearchContent();
        } else {
            this.showSearchEmpty();
        }
    },

    // Initialize notifications
    initNotifications() {
        const notificationBell = document.getElementById('notificationBell');
        const notificationDropdown = document.getElementById('notificationDropdown');

        if (notificationBell && notificationDropdown) {
            // Load notifications on bell click
            notificationBell.addEventListener('click', () => {
                this.loadNotifications();
            });
        }

        // Auto-refresh notifications every 5 minutes
        setInterval(() => {
            this.refreshNotificationCount();
        }, 300000);
    },

    // Load notifications
    loadNotifications() {
        // Implementation for loading notifications
        console.log('Loading notifications...');
    },

    // Refresh notification count
    refreshNotificationCount() {
        // Implementation for refreshing notification count
        console.log('Refreshing notification count...');
    },

    // Initialize tooltips and popovers
    initTooltips() {
        // Initialize Bootstrap tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });

        // Initialize Bootstrap popovers
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function(popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    },

    // Initialize modals
    initModals() {
        // Auto-focus first input in modals
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('shown.bs.modal', () => {
                const firstInput = modal.querySelector('input:not([type="hidden"]), textarea, select');
                if (firstInput) {
                    firstInput.focus();
                }
            });
        });
    },

    // Initialize data tables
    initTables() {
        // Initialize sortable tables if DataTables is available
        if (typeof $ !== 'undefined' && $.fn.DataTable) {
            $('.data-table').DataTable({
                responsive: true,
                pageLength: 25,
                language: {
                    search: "Search:",
                    lengthMenu: "Show _MENU_ entries",
                    info: "Showing _START_ to _END_ of _TOTAL_ entries",
                    paginate: {
                        first: "First",
                        last: "Last",
                        next: "Next",
                        previous: "Previous"
                    }
                }
            });
        }
    },

    // Initialize charts if needed
    initCharts() {
        // Chart initialization logic would go here
        console.log('Charts initialized');
    },

    // Initialize scroll to top button
    initScrollToTop() {
        const scrollToTopBtn = document.getElementById('scrollToTop');
        
        if (scrollToTopBtn) {
            window.addEventListener('scroll', () => {
                if (window.scrollY > 300) {
                    scrollToTopBtn.classList.add('show');
                } else {
                    scrollToTopBtn.classList.remove('show');
                }
            });

            scrollToTopBtn.addEventListener('click', () => {
                window.scrollTo({
                    top: 0,
                    behavior: 'smooth'
                });
            });
        }
    },

    // Initialize theme toggle
    initThemeToggle() {
        const themeToggle = document.getElementById('themeToggle');
        
        if (themeToggle) {
            // Load saved theme
            const savedTheme = localStorage.getItem('dashboard-theme') || 'light';
            document.body.setAttribute('data-theme', savedTheme);
            
            themeToggle.addEventListener('click', () => {
                const currentTheme = document.body.getAttribute('data-theme');
                const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
                
                document.body.setAttribute('data-theme', newTheme);
                localStorage.setItem('dashboard-theme', newTheme);
            });
        }
    },

    // Initialize language switcher
    initLanguageSwitcher() {
        const languageLinks = document.querySelectorAll('.language-link');
        
        languageLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const langCode = link.getAttribute('data-lang');
                this.switchLanguage(langCode);
            });
        });
    },

    // Switch language
    switchLanguage(langCode) {
        // Implementation for language switching
        console.log('Switching to language:', langCode);
        // This would typically submit a form to change language
    },

    // Utility functions
    showToast(message, type = 'info') {
        const toastContainer = document.querySelector('.toast-container') || this.createToastContainer();
        
        const toast = document.createElement('div');
        toast.className = 'toast show';
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="toast-header">
                <strong class="me-auto">
                    <i class="fas fa-${this.getToastIcon(type)} text-${type}"></i>
                    Notification
                </strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">${message}</div>
        `;
        
        toastContainer.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            toast.remove();
        }, 5000);
    },

    createToastContainer() {
        const container = document.createElement('div');
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1200';
        document.body.appendChild(container);
        return container;
    },

    getToastIcon(type) {
        const icons = {
            'success': 'check-circle',
            'error': 'exclamation-triangle',
            'warning': 'exclamation-circle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }
};

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    DashboardComponents.init();
});

// Export for use in other scripts
window.DashboardComponents = DashboardComponents;