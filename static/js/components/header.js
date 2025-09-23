/**
 * Clean Header/Navbar JavaScript
 * Modern vanilla JavaScript approach for header functionality
 * Handles search, notifications, user dropdown, and responsive behavior
 */

class HeaderManager {
    constructor() {
        this.header = null;
        this.searchBox = null;
        this.notificationDropdown = null;
        this.userDropdown = null;
        this.searchTimeout = null;
        this.notificationCount = 0;

        // Initialize when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    init() {
        this.header = document.querySelector('.main-header');
        this.searchBox = document.getElementById('globalSearch');
        this.notificationDropdown = document.querySelector('.notification-dropdown');
        this.userDropdown = document.querySelector('.header-right .dropdown');

        if (!this.header) {
            console.warn('Header element not found');
            return;
        }

        this.setupSearchFunctionality();
        this.setupNotifications();
        this.setupUserDropdown();
        this.setupResponsiveHeader();
        this.setupKeyboardNavigation();

        console.log('Clean Header initialized successfully');
    }

    setupSearchFunctionality() {
        if (!this.searchBox) return;

        // Real-time search with debouncing
        this.searchBox.addEventListener('input', (e) => {
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => {
                this.performSearch(e.target.value);
            }, 300);
        });

        // Handle search form submission
        const searchForm = this.searchBox.closest('.search-box');
        if (searchForm) {
            const searchButton = searchForm.querySelector('.btn');
            if (searchButton) {
                searchButton.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.performSearch(this.searchBox.value);
                });
            }
        }

        // Handle Enter key
        this.searchBox.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.performSearch(e.target.value);
            }
        });
    }

    performSearch(query) {
        if (!query.trim()) return;

        // Show loading state
        this.showSearchLoading();

        // Perform HTMX search or redirect to search page
        const searchUrl = '/search/';
        const params = new URLSearchParams({ q: query });

        // If HTMX is available, use it
        if (typeof htmx !== 'undefined') {
            htmx.ajax('GET', `${searchUrl}?${params}`, {
                target: '#search-results',
                swap: 'innerHTML'
            });
        } else {
            // Fallback to regular navigation
            window.location.href = `${searchUrl}?${params}`;
        }
    }

    showSearchLoading() {
        if (!this.searchBox) return;

        const originalPlaceholder = this.searchBox.placeholder;
        this.searchBox.placeholder = 'Searching...';
        this.searchBox.disabled = true;

        setTimeout(() => {
            this.searchBox.placeholder = originalPlaceholder;
            this.searchBox.disabled = false;
        }, 1000);
    }

    setupNotifications() {
        if (!this.notificationDropdown) return;

        // Handle notification dropdown toggle
        const notificationButton = this.notificationDropdown.querySelector('.btn');
        if (notificationButton) {
            notificationButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleNotifications();
            });
        }

        // Mark notifications as read when opened
        this.notificationDropdown.addEventListener('shown.bs.dropdown', () => {
            this.markNotificationsAsViewed();
        });

        // Handle individual notification clicks
        const notificationItems = this.notificationDropdown.querySelectorAll('.dropdown-item');
        notificationItems.forEach(item => {
            item.addEventListener('click', (e) => {
                this.handleNotificationClick(e, item);
            });
        });

        // Auto-refresh notifications every 30 seconds
        setInterval(() => {
            this.refreshNotifications();
        }, 30000);
    }

    toggleNotifications() {
        const dropdown = new bootstrap.Dropdown(this.notificationDropdown.querySelector('.btn'));
        dropdown.toggle();
    }

    markNotificationsAsViewed() {
        const badge = this.notificationDropdown.querySelector('.notification-badge');
        if (badge) {
            // Animate badge removal
            badge.style.transform = 'scale(0)';
            setTimeout(() => {
                badge.style.display = 'none';
            }, 150);
        }

        // Send AJAX request to mark as viewed
        if (typeof htmx !== 'undefined') {
            htmx.ajax('POST', '/notifications/mark-viewed/', {
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrf-token]')?.content || ''
                }
            });
        }
    }

    handleNotificationClick(e, item) {
        const notificationId = item.dataset.notificationId;
        if (notificationId) {
            // Mark specific notification as read
            this.markNotificationAsRead(notificationId);
        }
    }

    markNotificationAsRead(notificationId) {
        if (typeof htmx !== 'undefined') {
            htmx.ajax('POST', `/notifications/${notificationId}/mark-read/`, {
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrf-token]')?.content || ''
                }
            });
        }
    }

    refreshNotifications() {
        if (typeof htmx !== 'undefined' && this.notificationDropdown) {
            htmx.ajax('GET', '/notifications/header-count/', {
                target: '.notification-dropdown',
                swap: 'outerHTML'
            });
        }
    }

    setupUserDropdown() {
        if (!this.userDropdown) return;

        const userButton = this.userDropdown.querySelector('.dropdown-toggle');
        if (!userButton) return;

        // Handle user profile image error
        const userImage = userButton.querySelector('img');
        if (userImage) {
            userImage.addEventListener('error', () => {
                userImage.style.display = 'none';
                // Show initials or default icon instead
                const initials = this.getUserInitials();
                const fallback = document.createElement('div');
                fallback.className = 'user-avatar-fallback';
                fallback.textContent = initials;
                fallback.style.cssText = `
                    width: 32px; height: 32px; border-radius: 50%;
                    background: rgba(255,255,255,0.2); color: white;
                    display: flex; align-items: center; justify-content: center;
                    font-size: 14px; font-weight: 600;
                `;
                userImage.parentNode.insertBefore(fallback, userImage);
            });
        }

        // Handle logout confirmation
        const logoutLink = this.userDropdown.querySelector('a[href*="logout"]');
        if (logoutLink) {
            logoutLink.addEventListener('click', (e) => {
                if (!confirm('Are you sure you want to log out?')) {
                    e.preventDefault();
                }
            });
        }
    }

    getUserInitials() {
        const userNameElement = this.userDropdown.querySelector('.fw-semibold');
        if (userNameElement) {
            const name = userNameElement.textContent.trim();
            return name.split(' ').map(word => word[0]).join('').toUpperCase().slice(0, 2);
        }
        return 'U';
    }

    setupResponsiveHeader() {
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                this.handleHeaderResize();
            }, 100);
        });

        // Initial setup
        this.handleHeaderResize();
    }

    handleHeaderResize() {
        const windowWidth = window.innerWidth;

        // Mobile breakpoint handling
        if (windowWidth <= 768) {
            this.enableMobileMode();
        } else {
            this.enableDesktopMode();
        }
    }

    enableMobileMode() {
        if (this.searchBox) {
            this.searchBox.closest('.search-box')?.classList.add('d-none');
        }

        // Collapse user info text on mobile
        const userText = this.userDropdown?.querySelector('.d-none.d-md-block');
        if (userText) {
            userText.classList.add('d-none');
        }
    }

    enableDesktopMode() {
        if (this.searchBox) {
            this.searchBox.closest('.search-box')?.classList.remove('d-none');
        }

        // Show user info text on desktop
        const userText = this.userDropdown?.querySelector('.d-none.d-md-block');
        if (userText) {
            userText.classList.remove('d-none');
        }
    }

    setupKeyboardNavigation() {
        // Handle keyboard navigation for dropdowns
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                // Close all open dropdowns
                const openDropdowns = document.querySelectorAll('.dropdown-menu.show');
                openDropdowns.forEach(dropdown => {
                    const toggle = dropdown.previousElementSibling;
                    if (toggle) {
                        const bsDropdown = bootstrap.Dropdown.getInstance(toggle);
                        if (bsDropdown) {
                            bsDropdown.hide();
                        }
                    }
                });
            }
        });

        // Tab navigation improvements
        const focusableElements = this.header.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );

        focusableElements.forEach(element => {
            element.addEventListener('keydown', (e) => {
                if (e.key === 'Tab') {
                    // Custom tab navigation if needed
                    this.handleTabNavigation(e, element, focusableElements);
                }
            });
        });
    }

    handleTabNavigation(e, currentElement, focusableElements) {
        // Implementation for enhanced tab navigation if needed
        // This is where you could add circular tab navigation within dropdowns
    }

    // Public API methods
    updateNotificationCount(count) {
        this.notificationCount = count;
        const badge = this.notificationDropdown?.querySelector('.notification-badge');
        if (badge) {
            if (count > 0) {
                badge.textContent = count > 99 ? '99+' : count.toString();
                badge.style.display = 'flex';
            } else {
                badge.style.display = 'none';
            }
        }
    }

    showHeaderMessage(message, type = 'info', duration = 3000) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        messageDiv.style.cssText = `
            top: calc(var(--header-height) + 10px);
            right: 20px;
            z-index: 1070;
            min-width: 300px;
        `;
        messageDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(messageDiv);

        // Auto remove after duration
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.remove();
            }
        }, duration);
    }
}

// Initialize header when script loads
const headerManager = new HeaderManager();

// Export for potential use in other scripts
if (typeof window !== 'undefined') {
    window.HeaderManager = headerManager;
}

// HTMX compatibility
document.addEventListener('htmx:afterSwap', () => {
    if (window.HeaderManager) {
        window.HeaderManager.setupNotifications();
        window.HeaderManager.setupUserDropdown();
    }
});

// Alpine.js compatibility
document.addEventListener('alpine:init', () => {
    if (typeof Alpine !== 'undefined') {
        Alpine.data('header', () => ({
            searchQuery: '',
            notificationCount: 0,

            init() {
                this.notificationCount = parseInt(
                    document.querySelector('.notification-badge')?.textContent || '0'
                );
            },

            performSearch() {
                if (window.HeaderManager) {
                    window.HeaderManager.performSearch(this.searchQuery);
                }
            },

            updateNotifications(count) {
                this.notificationCount = count;
                if (window.HeaderManager) {
                    window.HeaderManager.updateNotificationCount(count);
                }
            }
        }));
    }
});
