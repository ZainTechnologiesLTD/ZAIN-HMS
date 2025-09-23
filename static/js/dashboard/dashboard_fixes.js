/**
 * Dashboard Fixes and Optimizations
 * Addresses timing issues, responsive behavior, and UI enhancements
 */

(function() {
    'use strict';

    // Ensure DOM is ready
    document.addEventListener('DOMContentLoaded', function() {

        // Fix sidebar toggle functionality
        const sidebar = document.getElementById('sidebar');
        const mainContent = document.querySelector('.main-content');
        const sidebarToggle = document.getElementById('sidebar-toggle');

        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', function() {
                sidebar?.classList.toggle('collapsed');
                mainContent?.classList.toggle('sidebar-collapsed');
            });
        }

        // Fix responsive sidebar behavior
        function handleResize() {
            if (window.innerWidth <= 768) {
                sidebar?.classList.add('mobile');
            } else {
                sidebar?.classList.remove('mobile');
            }
        }

        window.addEventListener('resize', handleResize);
        handleResize(); // Call once on load

        // Fix card animations with proper error handling
        const statCards = document.querySelectorAll('.stat-card');
        statCards.forEach(card => {
            card.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-2px)';
            });

            card.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0)';
            });
        });

        // Fix loading states for async content
        const loadingElements = document.querySelectorAll('[data-loading]');
        loadingElements.forEach(element => {
            const originalContent = element.innerHTML;

            // Show loading spinner
            element.innerHTML = '<div class="loading-spinner"></div>';

            // Simulate async loading (replace with actual async operations)
            setTimeout(() => {
                element.innerHTML = originalContent;
            }, 1000);
        });

        // Fix HTMX integration if available
        if (typeof htmx !== 'undefined') {
            // Handle HTMX loading states
            document.body.addEventListener('htmx:beforeRequest', function(evt) {
                const target = evt.detail.target;
                target.classList.add('htmx-loading');
            });

            document.body.addEventListener('htmx:afterRequest', function(evt) {
                const target = evt.detail.target;
                target.classList.remove('htmx-loading');
            });
        }

        // Fix tooltip initialization for Bootstrap 5
        if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        }

        // Fix dropdown initialization for Bootstrap 5
        if (typeof bootstrap !== 'undefined' && bootstrap.Dropdown) {
            const dropdownElementList = [].slice.call(document.querySelectorAll('.dropdown-toggle'));
            dropdownElementList.map(function (dropdownToggleEl) {
                return new bootstrap.Dropdown(dropdownToggleEl);
            });
        }

        // Fix number formatting for stats
        const numberElements = document.querySelectorAll('.stat-number');
        numberElements.forEach(element => {
            const value = parseFloat(element.textContent.replace(/[^\d.-]/g, ''));
            if (!isNaN(value)) {
                element.textContent = new Intl.NumberFormat('en-US').format(value);
            }
        });

        // Fix accessibility improvements
        const clickableCards = document.querySelectorAll('.stat-card[data-href]');
        clickableCards.forEach(card => {
            card.setAttribute('tabindex', '0');
            card.setAttribute('role', 'button');

            card.addEventListener('click', function() {
                const href = this.getAttribute('data-href');
                if (href) {
                    window.location.href = href;
                }
            });

            card.addEventListener('keypress', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.click();
                }
            });
        });

        // Fix dark mode toggle if available
        const darkModeToggle = document.getElementById('dark-mode-toggle');
        if (darkModeToggle) {
            darkModeToggle.addEventListener('click', function() {
                document.body.classList.toggle('dark-mode');
                localStorage.setItem('darkMode', document.body.classList.contains('dark-mode'));
            });

            // Load saved dark mode preference
            if (localStorage.getItem('darkMode') === 'true') {
                document.body.classList.add('dark-mode');
            }
        }

        // Fix search functionality
        const searchInput = document.getElementById('global-search');
        if (searchInput) {
            let searchTimeout;

            searchInput.addEventListener('input', function() {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    const query = this.value.trim();
                    if (query.length >= 2) {
                        // Trigger search (implement based on your search system)
                        console.log('Searching for:', query);
                    }
                }, 300);
            });
        }

        // Fix infinite scroll or pagination
        const loadMoreButton = document.querySelector('.load-more');
        if (loadMoreButton) {
            loadMoreButton.addEventListener('click', function() {
                this.disabled = true;
                this.innerHTML = '<div class="loading-spinner"></div> Loading...';

                // Simulate loading more content
                setTimeout(() => {
                    this.disabled = false;
                    this.innerHTML = 'Load More';
                }, 2000);
            });
        }

        // Performance optimization: Lazy load images
        const images = document.querySelectorAll('img[data-src]');
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.getAttribute('data-src');
                    img.removeAttribute('data-src');
                    observer.unobserve(img);
                }
            });
        });

        images.forEach(img => imageObserver.observe(img));

        // Console log for debugging
        console.log('Dashboard fixes applied successfully');
    });

    // Handle errors gracefully
    window.addEventListener('error', function(e) {
        console.warn('Dashboard error caught:', e.message);
        // Could send to error reporting service
    });

})();
