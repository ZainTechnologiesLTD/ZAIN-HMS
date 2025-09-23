/**
 * ZAIN HMS - Dashboard JavaScript
 * Consolidated dashboard JS following naming conventions
 * Version: 3.0 - Modern ES6+ Implementation with performance optimization
 */

class Dashboard {
    constructor() {
        this.config = {
            refreshInterval: 30000, // 30 seconds
            animationDuration: 300,
            debounceDelay: 250,
            maxRetries: 3
        };

        this.cache = new Map();
        this.observers = new Map();
        this.abortController = new AbortController();

        this.init();
    }

    /**
     * Initialize dashboard functionality
     */
    init() {
        this.setupEventListeners();
        this.initializeAnimations();
        this.setupIntersectionObserver();
        this.initializeCharts();
        this.setupKeyboardNavigation();
        this.startAutoRefresh();

        // Legacy support
        this.initLegacyStatCards();

        console.log('Dashboard initialized successfully');
    }

    /**
     * Setup event listeners with modern patterns
     */
    setupEventListeners() {
        // Use event delegation for better performance
        document.addEventListener('click', this.handleClick.bind(this));
        document.addEventListener('keydown', this.handleKeyboard.bind(this));

        // Debounced resize handler
        window.addEventListener('resize', this.debounce(this.handleResize.bind(this), this.config.debounceDelay));

        // Cleanup on page unload
        window.addEventListener('beforeunload', this.cleanup.bind(this));

        // Handle visibility change for auto-refresh
        document.addEventListener('visibilitychange', this.handleVisibilityChange.bind(this));
    }

    /**
     * Handle click events with delegation
     */
    handleClick(event) {
        const target = event.target.closest('[data-action]');
        if (!target) return;

        const action = target.dataset.action;
        const method = this[`handle${action.charAt(0).toUpperCase() + action.slice(1)}`];

        if (typeof method === 'function') {
            method.call(this, event, target);
        }
    }

    /**
     * Handle keyboard navigation
     */
    handleKeyboard(event) {
        if (event.key === 'Escape') {
            this.closeModals();
        }

        // Arrow key navigation for action items
        if (event.key === 'ArrowRight' || event.key === 'ArrowLeft') {
            this.navigateActionItems(event);
        }
    }

    /**
     * Navigate action items with keyboard
     */
    navigateActionItems(event) {
        const items = document.querySelectorAll('.quick-action-item, .tool-btn');
        const currentIndex = Array.from(items).findIndex(item => item === document.activeElement);

        if (currentIndex === -1) return;

        let nextIndex = currentIndex;
        if (event.key === 'ArrowRight') {
            nextIndex = Math.min(currentIndex + 1, items.length - 1);
        } else if (event.key === 'ArrowLeft') {
            nextIndex = Math.max(currentIndex - 1, 0);
        }

        items[nextIndex]?.focus();
        event.preventDefault();
    }

    /**
     * Initialize animations with Intersection Observer
     */
    setupIntersectionObserver() {
        if (!window.IntersectionObserver) return;

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('animate-in');
                        this.animateCounter(entry.target);
                    }
                });
            },
            { threshold: 0.1, rootMargin: '50px' }
        );

        // Observe KPI cards and stats
        document.querySelectorAll('.kpi-card, .stat-card').forEach(card => {
            observer.observe(card);
        });

        this.observers.set('intersection', observer);
    }

    /**
     * Animate counter values
     */
    animateCounter(element) {
        const valueElement = element.querySelector('.kpi-value, .stat-value, .value');
        if (!valueElement || valueElement.dataset.animated) return;

        const finalValue = valueElement.textContent.replace(/[^0-9.-]/g, '');
        const numericValue = parseFloat(finalValue);

        if (isNaN(numericValue)) return;

        valueElement.dataset.animated = 'true';
        const duration = 1500;
        const startTime = performance.now();
        const startValue = 0;

        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Easing function
            const easeOutQuart = 1 - Math.pow(1 - progress, 4);
            const currentValue = startValue + (numericValue - startValue) * easeOutQuart;

            // Format the value based on original format
            const originalText = valueElement.textContent;
            if (originalText.includes('$')) {
                valueElement.textContent = '$' + Math.floor(currentValue).toLocaleString();
            } else if (originalText.includes('%')) {
                valueElement.textContent = Math.floor(currentValue) + '%';
            } else {
                valueElement.textContent = Math.floor(currentValue).toLocaleString();
            }

            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }

    /**
     * Initialize animations
     */
    initializeAnimations() {
        // Add CSS for animations without hiding by default
        const style = document.createElement('style');
        style.textContent = `
            .kpi-card, .stat-card, .main-card {
                transition: opacity 0.6s ease, transform 0.6s ease;
            }
            .animate-in {
                opacity: 1;
                transform: translateY(0);
            }
        `;
        document.head.appendChild(style);
        // Ensure existing elements are visible
        document.querySelectorAll('.kpi-card, .stat-card, .main-card').forEach(el => el.classList.add('animate-in'));
    }

    /**
     * Initialize charts if Chart.js is available
     */
    initializeCharts() {
        if (typeof Chart === 'undefined') {
            console.log('Chart.js not loaded, skipping chart initialization');
            return;
        }

        // Charts will be initialized by the inline script in the template
        // This method can be used for additional chart customization
        this.setupChartDefaults();
    }

    /**
     * Setup Chart.js defaults
     */
    setupChartDefaults() {
        if (typeof Chart === 'undefined') return;

        Chart.defaults.font.family = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
        Chart.defaults.font.size = 12;
        Chart.defaults.color = '#6b7280';

        // Responsive settings
        Chart.defaults.responsive = true;
        Chart.defaults.maintainAspectRatio = false;
    }

    /**
     * Setup keyboard navigation
     */
    setupKeyboardNavigation() {
        const focusableElements = document.querySelectorAll('.quick-action-item, .tool-btn, .django-admin-link');

        focusableElements.forEach(element => {
            if (!element.hasAttribute('tabindex')) {
                element.setAttribute('tabindex', '0');
            }

            // Add keyboard support
            element.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    element.click();
                }
            });
        });
    }

    /**
     * Start auto-refresh
     */
    startAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }

        this.refreshTimer = setInterval(() => {
            if (!document.hidden) {
                this.refreshStats();
            }
        }, this.config.refreshInterval);
    }

    /**
     * Handle visibility change
     */
    handleVisibilityChange() {
        if (document.hidden) {
            this.pauseAnimations();
        } else {
            this.resumeAnimations();
            this.refreshStats();
        }
    }

    /**
     * Refresh statistics
     */
    async refreshStats() {
        try {
            console.log('Stats refreshed at:', new Date().toLocaleTimeString());
            // Add actual refresh logic here if needed
        } catch (error) {
            console.error('Error refreshing stats:', error);
        }
    }

    /**
     * Handle window resize
     */
    handleResize() {
        // Debounced resize handling
        this.updateLayout();
    }

    /**
     * Update layout after resize
     */
    updateLayout() {
        // Update chart sizes if they exist
        if (typeof Chart !== 'undefined') {
            Chart.helpers.each(Chart.instances, (instance) => {
                instance.resize();
            });
        }
    }

    /**
     * Pause animations when page is hidden
     */
    pauseAnimations() {
        document.querySelectorAll('.animate-in').forEach(element => {
            element.style.animationPlayState = 'paused';
        });
    }

    /**
     * Resume animations when page is visible
     */
    resumeAnimations() {
        document.querySelectorAll('.animate-in').forEach(element => {
            element.style.animationPlayState = 'running';
        });
    }

    /**
     * Close any open modals
     */
    closeModals() {
        // Close modals or overlays if any
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            const bootstrapModal = bootstrap.Modal.getInstance(modal);
            if (bootstrapModal) {
                bootstrapModal.hide();
            }
        });
    }

    /**
     * Debounce utility function
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func.apply(this, args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Legacy support for old stat cards
     */
    initLegacyStatCards() {
        const statCards = document.querySelectorAll('.stat-card');
        statCards.forEach(card => {
            card.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-2px)';
                this.style.boxShadow = '0 6px 12px rgba(0, 0, 0, 0.15)';
            });

            card.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0)';
                this.style.boxShadow = 'none';
            });
        });
    }

    /**
     * Cleanup method
     */
    cleanup() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }

        if (this.abortController) {
            this.abortController.abort();
        }

        this.observers.forEach(observer => {
            observer.disconnect();
        });

        console.log('Dashboard cleanup completed');
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if we're on a dashboard page
    if (document.querySelector('.content-inner, .dashboard-container')) {
        window.dashboardInstance = new Dashboard();

        // After HTMX swaps, ensure new content is visible
        document.body.addEventListener('htmx:afterSwap', function(evt) {
            try {
                const root = evt.target || document;
                root.querySelectorAll('.kpi-card, .stat-card, .main-card').forEach(el => el.classList.add('animate-in'));
            } catch (_) {}
        });
    }
});

// Export for testing/external access
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Dashboard;
}
