/* ZAIN HMS - ENHANCED ADMIN UI JAVASCRIPT */

// Theme Management
class ZainAdminTheme {
    constructor() {
        this.currentTheme = localStorage.getItem('zain-admin-theme') || 'light';
        this.init();
    }

    init() {
        this.createThemeToggle();
        this.applyTheme();
        this.initializeEnhancements();
        this.initializeSearch();
        this.initializeDashboard();
    }

    createThemeToggle() {
        // Add theme toggle button to navbar
        const navbar = document.querySelector('.navbar .navbar-nav');
        if (navbar) {
            const themeToggle = document.createElement('li');
            themeToggle.className = 'nav-item';
            themeToggle.innerHTML = `
                <button class="btn btn-sm btn-outline-primary nav-link" id="theme-toggle">
                    <i class="fas fa-moon" id="theme-icon"></i>
                    <span class="d-none d-md-inline ms-1">Theme</span>
                </button>
            `;
            navbar.appendChild(themeToggle);

            document.getElementById('theme-toggle').addEventListener('click', () => {
                this.toggleTheme();
            });
        }
    }

    toggleTheme() {
        this.currentTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        localStorage.setItem('zain-admin-theme', this.currentTheme);
        this.applyTheme();
    }

    applyTheme() {
        const body = document.body;
        const themeIcon = document.getElementById('theme-icon');
        
        if (this.currentTheme === 'dark') {
            body.classList.add('dark-mode');
            if (themeIcon) themeIcon.className = 'fas fa-sun';
        } else {
            body.classList.remove('dark-mode');
            if (themeIcon) themeIcon.className = 'fas fa-moon';
        }
    }

    initializeEnhancements() {
        // Add loading animation to forms
        this.enhanceForms();
        
        // Add confirmation dialogs
        this.addConfirmDialogs();
        
        // Enhance tables
        this.enhanceTables();
        
        // Add keyboard shortcuts
        this.initKeyboardShortcuts();
        
        // Initialize tooltips
        this.initTooltips();
    }

    enhanceForms() {
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', function(e) {
                const submitBtn = form.querySelector('input[type="submit"], button[type="submit"]');
                if (submitBtn) {
                    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
                    submitBtn.disabled = true;
                }
            });
        });

        // Auto-save for textareas
        const textareas = document.querySelectorAll('textarea');
        textareas.forEach(textarea => {
            let timeout;
            textarea.addEventListener('input', function() {
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    this.setAttribute('data-saved', 'true');
                    // Show saved indicator
                    this.style.borderColor = '#28a745';
                    setTimeout(() => {
                        this.style.borderColor = '';
                    }, 2000);
                }, 2000);
            });
        });
    }

    addConfirmDialogs() {
        // Add confirmation for delete actions
        const deleteLinks = document.querySelectorAll('a[href*="delete"], input[value*="delete"]');
        deleteLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                    e.preventDefault();
                }
            });
        });
    }

    enhanceTables() {
        const tables = document.querySelectorAll('table');
        tables.forEach(table => {
            // Add hover effects
            table.classList.add('table-hover');
            
            // Make tables responsive
            if (!table.closest('.table-responsive')) {
                const wrapper = document.createElement('div');
                wrapper.className = 'table-responsive';
                table.parentNode.insertBefore(wrapper, table);
                wrapper.appendChild(table);
            }
        });
    }

    initKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            // Ctrl/Cmd + S to save
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault();
                const saveBtn = document.querySelector('input[name="_save"], input[name="_continue"]');
                if (saveBtn) {
                    saveBtn.click();
                }
            }
            
            // Ctrl/Cmd + K for quick search
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                const searchInput = document.querySelector('#searchbar');
                if (searchInput) {
                    searchInput.focus();
                }
            }
        });
    }

    initTooltips() {
        // Initialize Bootstrap tooltips if available
        if (typeof bootstrap !== 'undefined') {
            const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
            const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
        }
    }

    initializeSearch() {
        // Enhanced search functionality
        const searchInput = document.querySelector('#searchbar');
        if (searchInput) {
            // Add search suggestions
            this.createSearchSuggestions(searchInput);
            
            // Add recent searches
            this.loadRecentSearches(searchInput);
        }
    }

    createSearchSuggestions(searchInput) {
        const wrapper = document.createElement('div');
        wrapper.className = 'search-suggestions';
        searchInput.parentNode.insertBefore(wrapper, searchInput.nextSibling);

        searchInput.addEventListener('input', function() {
            if (this.value.length > 2) {
                // Simulate search suggestions (in real app, make API call)
                const suggestions = [
                    'Patients',
                    'Appointments',
                    'Doctors',
                    'Bills',
                    'Medicines'
                ].filter(item => item.toLowerCase().includes(this.value.toLowerCase()));

                wrapper.innerHTML = suggestions.map(suggestion => 
                    `<div class="suggestion-item" data-value="${suggestion}">${suggestion}</div>`
                ).join('');
                wrapper.style.display = suggestions.length ? 'block' : 'none';
            } else {
                wrapper.style.display = 'none';
            }
        });

        // Handle suggestion clicks
        wrapper.addEventListener('click', function(e) {
            if (e.target.classList.contains('suggestion-item')) {
                searchInput.value = e.target.getAttribute('data-value');
                wrapper.style.display = 'none';
                // Trigger search
                searchInput.form.submit();
            }
        });
    }

    loadRecentSearches(searchInput) {
        const recentSearches = JSON.parse(localStorage.getItem('zain-recent-searches') || '[]');
        
        searchInput.addEventListener('focus', function() {
            if (recentSearches.length && !this.value) {
                const wrapper = this.parentNode.querySelector('.search-suggestions');
                if (wrapper) {
                    wrapper.innerHTML = `
                        <div class="suggestions-header">Recent Searches</div>
                        ${recentSearches.slice(0, 5).map(search => 
                            `<div class="suggestion-item recent" data-value="${search}">
                                <i class="fas fa-history"></i> ${search}
                            </div>`
                        ).join('')}
                    `;
                    wrapper.style.display = 'block';
                }
            }
        });

        // Save searches
        searchInput.form?.addEventListener('submit', function() {
            const query = searchInput.value.trim();
            if (query && !recentSearches.includes(query)) {
                recentSearches.unshift(query);
                localStorage.setItem('zain-recent-searches', JSON.stringify(recentSearches.slice(0, 10)));
            }
        });
    }

    initializeDashboard() {
        // Dashboard widgets and animations
        this.animateCounters();
        this.initializeCharts();
        this.addWidgetControls();
    }

    animateCounters() {
        const counters = document.querySelectorAll('[data-counter]');
        counters.forEach(counter => {
            const target = parseInt(counter.getAttribute('data-counter'));
            const duration = 2000; // 2 seconds
            const increment = target / (duration / 16); // 60 FPS
            let current = 0;

            const timer = setInterval(() => {
                current += increment;
                if (current >= target) {
                    current = target;
                    clearInterval(timer);
                }
                counter.textContent = Math.floor(current).toLocaleString();
            }, 16);
        });
    }

    initializeCharts() {
        // Initialize Chart.js charts if available
        const chartElements = document.querySelectorAll('[data-chart]');
        chartElements.forEach(element => {
            // Chart initialization would go here
            // This is a placeholder for actual chart implementation
            element.innerHTML = '<div class="chart-placeholder">Chart will be rendered here</div>';
        });
    }

    addWidgetControls() {
        // Add minimize/expand controls to dashboard widgets
        const widgets = document.querySelectorAll('.card');
        widgets.forEach(widget => {
            const header = widget.querySelector('.card-header');
            if (header) {
                const controls = document.createElement('div');
                controls.className = 'widget-controls';
                controls.innerHTML = `
                    <button class="btn btn-sm btn-outline-secondary widget-toggle" title="Minimize/Expand">
                        <i class="fas fa-minus"></i>
                    </button>
                `;
                header.appendChild(controls);

                controls.querySelector('.widget-toggle').addEventListener('click', function() {
                    const body = widget.querySelector('.card-body');
                    const icon = this.querySelector('i');
                    
                    if (body.style.display === 'none') {
                        body.style.display = '';
                        icon.className = 'fas fa-minus';
                    } else {
                        body.style.display = 'none';
                        icon.className = 'fas fa-plus';
                    }
                });
            }
        });
    }
}

// Utility Functions
class ZainAdminUtils {
    static showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show notification-toast`;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    static formatNumber(num) {
        return new Intl.NumberFormat().format(num);
    }

    static formatDate(date) {
        return new Intl.DateTimeFormat('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        }).format(new Date(date));
    }

    static debounce(func, delay) {
        let timeoutId;
        return function (...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(this, args), delay);
        };
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    new ZainAdminTheme();
    
    // Add global styles
    const style = document.createElement('style');
    style.textContent = `
        .notification-toast {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
        }
        
        .search-suggestions {
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: white;
            border: 1px solid #ddd;
            border-top: none;
            border-radius: 0 0 4px 4px;
            max-height: 200px;
            overflow-y: auto;
            z-index: 1000;
            display: none;
        }
        
        .suggestion-item {
            padding: 8px 12px;
            cursor: pointer;
            border-bottom: 1px solid #eee;
        }
        
        .suggestion-item:hover {
            background: #f8f9fa;
        }
        
        .suggestions-header {
            padding: 8px 12px;
            font-weight: bold;
            color: #666;
            background: #f8f9fa;
            border-bottom: 1px solid #ddd;
            font-size: 0.85em;
        }
        
        .widget-controls {
            float: right;
        }
        
        .chart-placeholder {
            text-align: center;
            padding: 40px;
            color: #666;
            background: #f8f9fa;
            border-radius: 4px;
        }
        
        .dark-mode {
            --bg: #1a202c;
            --surface: #2d3748;
            --text: #e2e8f0;
            --border: #4a5568;
        }
        
        .dark-mode .search-suggestions {
            background: var(--surface);
            border-color: var(--border);
            color: var(--text);
        }
        
        .dark-mode .suggestion-item:hover {
            background: rgba(255,255,255,0.1);
        }
    `;
    document.head.appendChild(style);
    
    console.log('Zain HMS Enhanced Admin UI Loaded Successfully');
});
