/*
 * ZAIN HMS - Public Pages Core JavaScript
 * Alpine.js initialization and global stores
 * Version: 2.0 - Modular, organized
 */

// ===== Initialize Alpine.js Data Components =====
document.addEventListener('alpine:init', () => {
    // Global Alpine.js stores
    Alpine.store('notifications', {
        items: [],
        add(notification) {
            const id = Date.now();
            this.items.push({
                id,
                ...notification,
                timestamp: new Date()
            });
            // Auto-remove after 5 seconds
            setTimeout(() => this.remove(id), 5000);
        },
        remove(id) {
            this.items = this.items.filter(item => item.id !== id);
        }
    });
});

// ===== Global Utilities =====
// Enhanced HTMX configurations
document.addEventListener('DOMContentLoaded', function() {
    // Configure HTMX
    if (typeof htmx !== 'undefined') {
        // Global HTMX event handlers
        htmx.on('htmx:beforeRequest', function(evt) {
            // Show loading state
            const target = evt.detail.target;
            if (target) {
                target.classList.add('loading');
            }
        });

        htmx.on('htmx:afterRequest', function(evt) {
            // Hide loading state
            const target = evt.detail.target;
            if (target) {
                target.classList.remove('loading');
            }
        });

        htmx.on('htmx:responseError', function(evt) {
            Alpine.store('notifications').add({
                message: 'An error occurred. Please try again.',
                type: 'error'
            });
        });
    }

    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});
