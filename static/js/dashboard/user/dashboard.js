/**
 * Dashboard Modern JavaScript
 * Enterprise-grade dashboard functionality with performance optimizations
 */

// Dashboard namespace
window.Dashboard = (function() {
    'use strict';

    // Configuration
    const config = {
        apiEndpoints: {
            stats: '/dashboard/api/stats/',
            activities: '/dashboard/api/activities/',
            charts: '/dashboard/api/charts/',
            notifications: '/dashboard/api/notifications/',
            tasks: '/dashboard/api/tasks/'
        },
        refreshIntervals: {
            stats: 30000,     // 30 seconds
            activities: 60000, // 1 minute
            notifications: 45000, // 45 seconds
            charts: 300000    // 5 minutes
        },
        animations: {
            duration: 300,
            easing: 'cubic-bezier(0.4, 0, 0.2, 1)'
        },
        chart: {
            colors: {
                primary: '#0d6efd',
                success: '#198754',
                warning: '#ffc107',
                danger: '#dc3545',
                info: '#0dcaf0',
                secondary: '#6c757d'
            }
        }
    };

    // Utility functions
    const utils = {
        // Debounce function for performance
        debounce(func, wait, immediate) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    timeout = null;
                    if (!immediate) func.apply(this, args);
                };
                const callNow = immediate && !timeout;
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
                if (callNow) func.apply(this, args);
            };
        },

        // Throttle function for scroll/resize events
        throttle(func, limit) {
            let inThrottle;
            return function(...args) {
                if (!inThrottle) {
                    func.apply(this, args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, limit);
                }
            };
        },

        // Format numbers with proper locale
        formatNumber(num, locale = 'en-US') {
            if (isNaN(num)) return '0';
            return new Intl.NumberFormat(locale).format(num);
        },

        // Format currency
        formatCurrency(amount, currency = 'USD', locale = 'en-US') {
            if (isNaN(amount)) return '$0';
            return new Intl.NumberFormat(locale, {
                style: 'currency',
                currency: currency
            }).format(amount);
        },

        // Safe JSON parse
        safeJsonParse(str) {
            try {
                return JSON.parse(str);
            } catch (e) {
                console.error('JSON parse error:', e);
                return null;
            }
        },

        // Get CSRF token
        getCsrfToken() {
            return document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        },

        // Show toast notification
        showToast(message, type = 'info', duration = 5000) {
            const toastContainer = document.getElementById('toast-container') || this.createToastContainer();
            const toast = this.createToast(message, type);
            toastContainer.appendChild(toast);

            // Trigger animation
            setTimeout(() => toast.classList.add('show'), 100);

            // Auto remove
            setTimeout(() => this.removeToast(toast), duration);
        },

        createToastContainer() {
            const container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'position-fixed top-0 end-0 p-3';
            container.style.zIndex = '1055';
            document.body.appendChild(container);
            return container;
        },

        createToast(message, type) {
            const toast = document.createElement('div');
            toast.className = `toast align-items-center text-white bg-${type} border-0 fade`;
            toast.setAttribute('role', 'alert');
            toast.innerHTML = `
                <div class="d-flex">
                    <div class="toast-body">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto"
                            onclick="Dashboard.utils.removeToast(this.closest('.toast'))"></button>
                </div>
            `;
            return toast;
        },

        removeToast(toast) {
            if (toast) {
                toast.classList.add('hide');
                setTimeout(() => toast.remove(), 300);
            }
        }
    };

    // API service for data fetching
    const api = {
        async fetch(url, options = {}) {
            const defaultOptions = {
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': utils.getCsrfToken()
                }
            };

            try {
                const response = await fetch(url, { ...defaultOptions, ...options });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    return await response.json();
                }

                return await response.text();
            } catch (error) {
                console.error('API fetch error:', error);
                utils.showToast(`Error: ${error.message}`, 'danger');
                throw error;
            }
        },

        async getStats() {
            return this.fetch(config.apiEndpoints.stats);
        },

        async getActivities() {
            return this.fetch(config.apiEndpoints.activities);
        },

        async getChartData(type = 'monthly', range = '30') {
            return this.fetch(`${config.apiEndpoints.charts}?type=${type}&range=${range}`);
        },

        async getNotifications() {
            return this.fetch(config.apiEndpoints.notifications);
        },

        async markNotificationRead(notificationId) {
            return this.fetch(`/notifications/mark-read/${notificationId}/`, {
                method: 'POST'
            });
        }
    };

    // Real-time data management
    const realTime = {
        intervals: {},

        start(component, callback, interval) {
            if (this.intervals[component]) {
                clearInterval(this.intervals[component]);
            }

            this.intervals[component] = setInterval(callback, interval);
        },

        stop(component) {
            if (this.intervals[component]) {
                clearInterval(this.intervals[component]);
                delete this.intervals[component];
            }
        },

        stopAll() {
            Object.keys(this.intervals).forEach(component => {
                this.stop(component);
            });
        }
    };

    // KPI Cards management
    const kpiCards = {
        init() {
            this.setupCounterAnimations();
            this.startRealTimeUpdates();
        },

        setupCounterAnimations() {
            const cards = document.querySelectorAll('.kpi-card');

            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const valueElement = entry.target.querySelector('.kpi-value');
                        if (valueElement && !valueElement.dataset.animated) {
                            this.animateCounter(valueElement);
                            valueElement.dataset.animated = 'true';
                        }
                    }
                });
            }, { threshold: 0.1 });

            cards.forEach(card => observer.observe(card));
        },

        animateCounter(element) {
            const target = parseInt(element.textContent.replace(/\D/g, ''));
            const duration = 2000;
            const start = performance.now();
            const prefix = element.textContent.replace(/[\d,]/g, '');

            const animate = (currentTime) => {
                const elapsed = currentTime - start;
                const progress = Math.min(elapsed / duration, 1);

                // Easing function
                const easeOutQuart = 1 - Math.pow(1 - progress, 4);
                const current = Math.floor(target * easeOutQuart);

                element.textContent = prefix + utils.formatNumber(current);

                if (progress < 1) {
                    requestAnimationFrame(animate);
                }
            };

            requestAnimationFrame(animate);
        },

        async updateData() {
            try {
                const stats = await api.getStats();
                this.renderKPIs(stats);
            } catch (error) {
                console.error('Failed to update KPI data:', error);
            }
        },

        renderKPIs(data) {
            const kpiCards = {
                'patients-total': data.total_patients,
                'appointments-today': data.todays_appointments,
                'revenue-month': data.monthly_revenue,
                'staff-active': data.active_staff
            };

            Object.entries(kpiCards).forEach(([id, value]) => {
                const element = document.querySelector(`[data-kpi="${id}"] .kpi-value`);
                if (element) {
                    const oldValue = parseInt(element.textContent.replace(/\D/g, ''));
                    if (oldValue !== value) {
                        element.classList.add('updating');
                        setTimeout(() => {
                            element.textContent = utils.formatNumber(value);
                            element.classList.remove('updating');
                        }, 200);
                    }
                }
            });
        },

        startRealTimeUpdates() {
            realTime.start('kpi', () => {
                this.updateData();
            }, config.refreshIntervals.stats);
        }
    };

    // Chart management
    const charts = {
        instances: {},

        init() {
            this.initPatientChart();
            this.initRevenueChart();
            this.initDepartmentChart();
            this.setupChartControls();
        },

        initPatientChart() {
            const ctx = document.getElementById('patientStatsChart');
            if (!ctx) return;

            this.instances.patients = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'New Patients',
                        data: [],
                        borderColor: config.chart.colors.primary,
                        backgroundColor: config.chart.colors.primary + '20',
                        tension: 0.4,
                        fill: true,
                        pointBackgroundColor: config.chart.colors.primary,
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2,
                        pointRadius: 6
                    }]
                },
                options: this.getCommonChartOptions()
            });
        },

        initRevenueChart() {
            const ctx = document.getElementById('revenueChart');
            if (!ctx) return;

            this.instances.revenue = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Revenue',
                        data: [],
                        backgroundColor: config.chart.colors.success + '80',
                        borderColor: config.chart.colors.success,
                        borderWidth: 2,
                        borderRadius: 8,
                        borderSkipped: false
                    }]
                },
                options: {
                    ...this.getCommonChartOptions(),
                    scales: {
                        ...this.getCommonChartOptions().scales,
                        y: {
                            ...this.getCommonChartOptions().scales.y,
                            ticks: {
                                callback: function(value) {
                                    return utils.formatCurrency(value);
                                }
                            }
                        }
                    }
                }
            });
        },

        initDepartmentChart() {
            const ctx = document.getElementById('departmentChart');
            if (!ctx) return;

            this.instances.departments = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: [],
                    datasets: [{
                        data: [],
                        backgroundColor: [
                            config.chart.colors.primary,
                            config.chart.colors.success,
                            config.chart.colors.warning,
                            config.chart.colors.info,
                            config.chart.colors.danger,
                            config.chart.colors.secondary
                        ],
                        borderWidth: 0,
                        hoverBorderWidth: 2,
                        hoverBorderColor: '#fff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                padding: 20,
                                usePointStyle: true,
                                font: {
                                    size: 12
                                }
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((context.parsed / total) * 100).toFixed(1);
                                    return `${context.label}: ${context.parsed} (${percentage}%)`;
                                }
                            }
                        }
                    },
                    cutout: '60%'
                }
            });
        },

        getCommonChartOptions() {
            return {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: 'rgba(255, 255, 255, 0.2)',
                        borderWidth: 1,
                        cornerRadius: 8,
                        displayColors: false
                    }
                },
                scales: {
                    x: {
                        display: true,
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: {
                                size: 11
                            }
                        }
                    },
                    y: {
                        display: true,
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)',
                            drawBorder: false
                        },
                        ticks: {
                            font: {
                                size: 11
                            }
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            };
        },

        setupChartControls() {
            const typeControls = document.querySelectorAll('input[name="chartType"]');
            const rangeControl = document.querySelector('select[x-model="dateRange"]');

            typeControls.forEach(control => {
                control.addEventListener('change', () => {
                    this.updateCharts(control.value, rangeControl?.value || '30');
                });
            });

            if (rangeControl) {
                rangeControl.addEventListener('change', () => {
                    const activeType = document.querySelector('input[name="chartType"]:checked')?.value || 'monthly';
                    this.updateCharts(activeType, rangeControl.value);
                });
            }
        },

        async updateCharts(type, range) {
            try {
                const data = await api.getChartData(type, range);

                if (this.instances.patients && data.patient_data) {
                    this.instances.patients.data.labels = data.patient_labels;
                    this.instances.patients.data.datasets[0].data = data.patient_data;
                    this.instances.patients.update('none'); // Prevent animation-based resizing
                    this.instances.patients.resize(); // Force proper resize
                }

                if (this.instances.revenue && data.revenue_data) {
                    this.instances.revenue.data.labels = data.revenue_labels;
                    this.instances.revenue.data.datasets[0].data = data.revenue_data;
                    this.instances.revenue.update('none'); // Prevent animation-based resizing
                    this.instances.revenue.resize(); // Force proper resize
                }

                if (this.instances.departments && data.department_data) {
                    this.instances.departments.data.labels = data.department_labels;
                    this.instances.departments.data.datasets[0].data = data.department_data;
                    this.instances.departments.update('none'); // Prevent animation-based resizing
                    this.instances.departments.resize(); // Force proper resize
                }
            } catch (error) {
                console.error('Failed to update charts:', error);
            }
        },

        // Add method to handle window resize events properly
        handleResize() {
            Object.values(this.instances).forEach(chart => {
                if (chart && typeof chart.resize === 'function') {
                    chart.resize();
                }
            });
        }
    };

    // Activity feed management
    const activityFeed = {
        init() {
            this.startRealTimeUpdates();
        },

        async updateData() {
            try {
                const activities = await api.getActivities();
                this.renderActivities(activities);
            } catch (error) {
                console.error('Failed to update activities:', error);
            }
        },

        renderActivities(data) {
            const container = document.querySelector('.activity-list');
            if (!container) return;

            // Implementation would go here to render new activities
            // This would typically involve updating the Alpine.js data
            if (window.Alpine && container._x_dataStack) {
                container._x_dataStack[0].activities = data.activities || [];
            }
        },

        startRealTimeUpdates() {
            realTime.start('activities', () => {
                this.updateData();
            }, config.refreshIntervals.activities);
        }
    };

    // Notification management
    const notifications = {
        init() {
            this.setupEventListeners();
            this.startRealTimeUpdates();
        },

        setupEventListeners() {
            // Listen for notification actions
            document.addEventListener('click', (e) => {
                if (e.target.matches('[data-action="mark-read"]')) {
                    const notificationId = e.target.dataset.notificationId;
                    this.markAsRead(notificationId);
                }
            });
        },

        async markAsRead(notificationId) {
            try {
                await api.markNotificationRead(notificationId);
                this.updateNotificationBadge();
            } catch (error) {
                console.error('Failed to mark notification as read:', error);
            }
        },

        updateNotificationBadge() {
            // Update notification count in UI
            const badge = document.querySelector('.notification-badge');
            if (badge) {
                const count = parseInt(badge.textContent) - 1;
                if (count > 0) {
                    badge.textContent = count;
                } else {
                    badge.style.display = 'none';
                }
            }
        },

        startRealTimeUpdates() {
            realTime.start('notifications', async () => {
                try {
                    const data = await api.getNotifications();
                    // Update notification UI
                    if (data.unread_count) {
                        const badge = document.querySelector('.notification-badge');
                        if (badge) {
                            badge.textContent = data.unread_count;
                            badge.style.display = 'flex';
                        }
                    }
                } catch (error) {
                    console.error('Failed to update notifications:', error);
                }
            }, config.refreshIntervals.notifications);
        }
    };

    // Keyboard shortcuts
    const keyboard = {
        init() {
            document.addEventListener('keydown', this.handleKeyPress.bind(this));
        },

        handleKeyPress(e) {
            // Ctrl/Cmd + K for quick search
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                this.triggerQuickSearch();
            }

            // Ctrl/Cmd + Shift + N for new patient
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'N') {
                e.preventDefault();
                window.location.href = '/patients/create/';
            }

            // Ctrl/Cmd + Shift + A for new appointment
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'A') {
                e.preventDefault();
                window.location.href = '/appointments/create/';
            }

            // Escape to close modals
            if (e.key === 'Escape') {
                this.closeModals();
            }
        },

        triggerQuickSearch() {
            // Trigger Alpine.js quick search modal
            const searchComponent = document.querySelector('[x-data*="quickSearch"]');
            if (searchComponent && searchComponent._x_dataStack) {
                searchComponent._x_dataStack[0].quickSearch = true;
            }
        },

        closeModals() {
            // Close any open modals
            const modals = document.querySelectorAll('.modal.show');
            modals.forEach(modal => {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) {
                    bsModal.hide();
                }
            });
        }
    };

    // Performance monitoring
    const performance = {
        init() {
            this.monitorPageLoad();
            this.monitorApiCalls();
        },

        monitorPageLoad() {
            window.addEventListener('load', () => {
                // Use Performance Observer API if available
                if ('PerformanceObserver' in window) {
                    const observer = new PerformanceObserver((list) => {
                        list.getEntries().forEach((entry) => {
                            console.log('Performance entry:', entry);
                        });
                    });
                    observer.observe({ entryTypes: ['navigation', 'resource'] });
                }
            });
        },

        monitorApiCalls() {
            // Monitor API response times
            const originalFetch = api.fetch;
            api.fetch = async function(...args) {
                const start = performance.now();
                try {
                    const result = await originalFetch.apply(this, args);
                    const end = performance.now();
                    console.log(`API call took ${end - start} milliseconds`);
                    return result;
                } catch (error) {
                    const end = performance.now();
                    console.error(`API call failed after ${end - start} milliseconds:`, error);
                    throw error;
                }
            };
        }
    };

    // Main initialization
    const init = () => {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', init);
            return;
        }

        console.log('Initializing Dashboard...');

        // Initialize components
        kpiCards.init();

        // Initialize charts only if Chart.js is loaded
        if (typeof Chart !== 'undefined') {
            charts.init();
        }

        activityFeed.init();
        notifications.init();
        keyboard.init();
        performance.init();

        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                realTime.stopAll();
            } else {
                // Restart real-time updates when page becomes visible
                kpiCards.startRealTimeUpdates();
                activityFeed.startRealTimeUpdates();
                notifications.startRealTimeUpdates();
            }
        });

        // Handle window resize for charts
        window.addEventListener('resize', utils.throttle(() => {
            charts.handleResize();
        }, 250));

        console.log('Dashboard initialized successfully');
    };

    // Cleanup function
    const destroy = () => {
        realTime.stopAll();

        // Destroy chart instances
        Object.values(charts.instances).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });

        console.log('Dashboard cleanup completed');
    };

    // Public API
    return {
        init,
        destroy,
        utils,
        api,
        kpiCards,
        charts,
        activityFeed,
        notifications,
        keyboard,
        performance,
        config
    };
})();

// Auto-initialize when script loads
Dashboard.init();

// Global cleanup on page unload
window.addEventListener('beforeunload', Dashboard.destroy);
