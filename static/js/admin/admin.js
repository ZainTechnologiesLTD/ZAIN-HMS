/**
 * ZAIN HMS - Admin Dashboard JavaScript
 * Alpine.js data functions and dashboard functionality
 * Version: 1.0
 */

/**
 * Alpine.js data function for admin dashboard
 * Provides reactive data and methods for the dashboard interface
 */
function adminDashboard() {
    return {
        // Reactive data properties
        isLoading: false,
        lastUpdated: new Date().toLocaleTimeString(),
        refreshInterval: null,
        chartReinitTimeout: null,
        autoRefresh: true,
        show: true,
        error: null,

        // Charts data
        chartsLoaded: false,
        chartsData: {},
        charts: {},

        // Stats data
        stats: {},

        // Initialize the dashboard
        init() {
            console.log('Admin Dashboard Alpine component initialized');
            try {
                this.updateLastUpdated();
                this.setupAutoRefresh();
                this.setupEventListeners();
                this.loadInitialData();
                this.initializeCharts().catch(error => {
                    console.error('Admin Dashboard: Chart initialization error:', error);
                }); // Initialize charts on startup
                
                // Register cleanup for page unload
                window.addEventListener('beforeunload', () => this.destroy());
            } catch (error) {
                console.error('Error initializing admin dashboard:', error);
                this.handleError('Failed to initialize dashboard');
            }
        },

        // Cleanup method for component destruction
        destroy() {
            console.log('Admin Dashboard: Component being destroyed, cleaning up...');
            
            // Clear refresh intervals
            if (this.refreshInterval) {
                clearInterval(this.refreshInterval);
                this.refreshInterval = null;
            }
            
            // Clear chart reinitialization timeout
            if (this.chartReinitTimeout) {
                clearTimeout(this.chartReinitTimeout);
                this.chartReinitTimeout = null;
            }
            
            // Destroy all charts
            this.destroyAllCharts();
            
            // Clear error states
            this.error = null;
            this.isLoading = false;
        },

        // Update the last updated timestamp
        updateLastUpdated() {
            this.lastUpdated = new Date().toLocaleTimeString();
        },

        // Update the current time display if it exists
        updateCurrentTime() {
            const timeElement = document.getElementById('current-time');
            if (timeElement) {
                const now = new Date();
                const timeString = now.toLocaleTimeString('en-US', {
                    hour: 'numeric',
                    minute: '2-digit',
                    hour12: true
                });
                timeElement.textContent = timeString;
            }
        },

        // Setup automatic refresh
        setupAutoRefresh() {
            if (this.autoRefresh) {
                this.refreshInterval = setInterval(() => {
                    if (!this.isLoading) {
                        this.refreshDashboard();
                    }
                }, 60000); // Refresh every 60 seconds (reduced from 30s)
            }
        },

        // Setup event listeners
        setupEventListeners() {
            // Listen for HTMX events
            document.addEventListener('htmx:beforeRequest', () => {
                this.isLoading = true;
            });

            document.addEventListener('htmx:afterRequest', () => {
                this.isLoading = false;
                this.updateLastUpdated();
            });

            document.addEventListener('htmx:responseError', (event) => {
                this.isLoading = false;
                this.handleError(`HTMX Error: ${event.detail.xhr.status}`);
                console.error('HTMX responseError:', event.detail);
            });

            // Listen for HTMX swap events to reinitialize charts with improved timing
            document.body.addEventListener('htmx:afterSwap', (event) => {
                // Re-initialize charts after HTMX updates with proper delay
                if (event.target.id === 'revenue-chart-container' || 
                    event.target.id === 'appointments-chart-container') {
                    console.log(`Admin Dashboard: HTMX swap detected for ${event.target.id}, scheduling chart reinitialization`);
                    
                    // Clear any existing timeout
                    if (this.chartReinitTimeout) {
                        clearTimeout(this.chartReinitTimeout);
                    }
                    
                    // Use a longer delay to ensure DOM is fully updated
                    this.chartReinitTimeout = setTimeout(() => {
                        console.log('Admin Dashboard: Executing delayed chart reinitialization');
                        this.destroyAllCharts(); // Full cleanup first
                        setTimeout(() => {
                            this.initializeCharts().catch(error => {
                                console.error('Admin Dashboard: Chart reinitialization error:', error);
                            }); // Then recreate
                        }, 50);
                    }, 250);
                }
            });

            // Listen for window resize
            window.addEventListener('resize', () => {
                this.handleResize();
            });
        },

        // Handle window resize
        handleResize() {
            if (this.charts) {
                Object.values(this.charts).forEach(chart => {
                    if (chart && typeof chart.resize === 'function') {
                        chart.resize();
                    }
                });
            }
        },

        // Load initial dashboard data
        loadInitialData() {
            // This can be used to load any initial data
            // For now, just update timestamp
            this.updateLastUpdated();
        },

        // Refresh the entire dashboard - simplified approach
        refreshDashboard() {
            if (this.isLoading) return;

            console.log('Dashboard refresh requested - updating timestamp only');

            // Just update the timestamp and let HTMX handle its own refresh cycles
            this.updateLastUpdated();
            this.updateCurrentTime();

            // Brief loading state for user feedback
            this.isLoading = true;
            setTimeout(() => {
                this.isLoading = false;
            }, 500);
        },

        // Handle errors
        handleError(message) {
            this.error = message;
            console.error('Dashboard error:', message);

            // Clear error after 5 seconds
            setTimeout(() => {
                this.error = null;
            }, 5000);
        },

        // Utility methods from the removed inline component
        formatCurrency(amount) {
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD'
            }).format(amount);
        },

        formatTime(date) {
            return date.toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit'
            });
        },

        reinitializeCharts() {
            // Reinitialize Chart.js instances after HTMX updates
            console.log('Admin Dashboard: Reinitializing charts...');
            setTimeout(() => {
                this.initializeCharts().catch(error => {
                    console.error('Admin Dashboard: Chart reinitialization error:', error);
                });
            }, 100);
        },

        // Initialize charts
        async initializeCharts() {
            console.log('Admin Dashboard: Initializing charts...');
            
            if (typeof Chart === 'undefined') {
                console.warn('Admin Dashboard: Chart.js not loaded, charts will not be available');
                return;
            }
            
            // Destroy all existing charts first to prevent conflicts
            this.destroyAllCharts();
            
            // Initialize revenue chart if canvas exists
            const revenueCanvas = document.getElementById('revenueChart');
            if (revenueCanvas) {
                try {
                    this.charts = this.charts || {};
                    this.charts.revenue = await this.createChart(revenueCanvas, {
                        type: 'line',
                        data: {
                            labels: [],
                            datasets: [{
                                label: 'Revenue',
                                data: [],
                                borderColor: 'rgb(34, 197, 94)',
                                backgroundColor: 'rgba(34, 197, 94, 0.1)',
                                borderWidth: 2,
                                fill: true,
                                tension: 0.4
                            }]
                        },
                        options: this.getChartOptions(true)
                    });
                    console.log('Admin Dashboard: Revenue chart initialized');
                } catch (error) {
                    console.error('Admin Dashboard: Failed to initialize revenue chart:', error);
                }
            }

            // Initialize appointments chart if canvas exists
            const appointmentsCanvas = document.getElementById('appointmentsChart');
            if (appointmentsCanvas) {
                try {
                    this.charts = this.charts || {};
                    this.charts.appointments = await this.createChart(appointmentsCanvas, {
                        type: 'bar',
                        data: {
                            labels: [],
                            datasets: [{
                                label: 'Appointments',
                                data: [],
                                borderColor: 'rgb(59, 130, 246)',
                                backgroundColor: 'rgba(59, 130, 246, 0.7)',
                                borderWidth: 2
                            }]
                        },
                        options: this.getChartOptions(false)
                    });
                    console.log('Admin Dashboard: Appointments chart initialized');
                } catch (error) {
                    console.error('Admin Dashboard: Failed to initialize appointments chart:', error);
                }
            }
        },

        // Destroy all existing charts with comprehensive cleanup
        destroyAllCharts() {
            console.log('Admin Dashboard: Comprehensive chart cleanup starting...');
            
            // Method 1: Destroy charts tracked by our component
            if (this.charts && typeof this.charts === 'object') {
                Object.keys(this.charts).forEach(key => {
                    if (this.charts[key] && typeof this.charts[key].destroy === 'function') {
                        try {
                            console.log(`Admin Dashboard: Destroying tracked ${key} chart`);
                            this.charts[key].destroy();
                        } catch (error) {
                            console.error(`Admin Dashboard: Error destroying tracked ${key} chart:`, error);
                        }
                        delete this.charts[key];
                    }
                });
                // Clear the charts object
                this.charts = {};
            }
            
            // Method 2: Destroy Chart.js instances using Chart.getChart()
            const canvasIds = ['revenueChart', 'appointmentsChart'];
            canvasIds.forEach(canvasId => {
                const canvas = document.getElementById(canvasId);
                if (canvas) {
                    const existingChart = Chart.getChart(canvas);
                    if (existingChart) {
                        try {
                            console.log(`Admin Dashboard: Found existing chart on ${canvasId}, destroying via Chart.getChart()`);
                            existingChart.destroy();
                        } catch (error) {
                            console.error(`Admin Dashboard: Error destroying chart via Chart.getChart() on ${canvasId}:`, error);
                        }
                    }
                }
            });
            
            // Method 3: Check for any remaining Chart.js instances (skip Chart.instances as it's not available in current version)
            // Just log that we're completed the available cleanup methods
            console.log('Admin Dashboard: Completed available Chart.js cleanup methods');
            
            // Method 4: Clear canvas elements manually
            canvasIds.forEach(canvasId => {
                const canvas = document.getElementById(canvasId);
                if (canvas) {
                    try {
                        const ctx = canvas.getContext('2d');
                        if (ctx) {
                            // Clear the canvas
                            ctx.clearRect(0, 0, canvas.width, canvas.height);
                            // Reset canvas state
                            ctx.setTransform(1, 0, 0, 1, 0, 0);
                        }
                        
                        // Remove Chart.js specific attributes
                        canvas.removeAttribute('data-chartjs-id');
                        delete canvas.chartInstance;
                        
                        // Reset canvas size to trigger proper reinitialization
                        const { width, height } = canvas.getBoundingClientRect();
                        canvas.width = width;
                        canvas.height = height;
                        
                        console.log(`Admin Dashboard: Canvas ${canvasId} manually cleaned`);
                    } catch (error) {
                        console.error(`Admin Dashboard: Error cleaning canvas ${canvasId}:`, error);
                    }
                }
            });
            
            console.log('Admin Dashboard: Comprehensive chart cleanup completed');
        },

        // Create chart with comprehensive error handling and cleanup
        async createChart(canvas, config) {
            try {
                // Validate inputs
                if (!canvas || !canvas.getContext) {
                    throw new Error('Invalid canvas element provided');
                }
                
                if (!config || typeof config !== 'object') {
                    throw new Error('Invalid chart configuration provided');
                }
                
                const ctx = canvas.getContext('2d');
                if (!ctx) {
                    throw new Error('Failed to get canvas 2D context');
                }
                
                const canvasId = canvas.id || 'unknown';
                console.log(`Admin Dashboard: Creating chart on canvas ${canvasId}`);
                
                // Comprehensive cleanup before chart creation
                // Method 1: Use Chart.js built-in method with aggressive cleanup
                let existingChart = Chart.getChart(canvas);
                if (existingChart) {
                    console.log(`Admin Dashboard: Found existing chart on canvas ${canvasId}, destroying it`);
                    try {
                        existingChart.destroy();
                    } catch (error) {
                        console.error(`Admin Dashboard: Error destroying existing chart:`, error);
                    }
                    // Clear the reference immediately
                    existingChart = null;
                }
                
                // Method 2: Wait a moment to ensure destruction is complete, then check again
                // This is necessary because Chart.js destruction might be asynchronous
                await new Promise(resolve => setTimeout(resolve, 50));
                
                // Double-check for any remaining chart
                existingChart = Chart.getChart(canvas);
                if (existingChart) {
                    console.log(`Admin Dashboard: Still found chart after delay, force destroying`);
                    try {
                        existingChart.destroy();
                        existingChart = null;
                    } catch (error) {
                        console.error(`Admin Dashboard: Error in delayed destroy:`, error);
                    }
                }
                
                // Method 3: Clear canvas completely
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.setTransform(1, 0, 0, 1, 0, 0);
                
                // Method 4: Reset canvas attributes that Chart.js might use
                canvas.removeAttribute('data-chartjs-id');
                delete canvas.chartInstance;
                
                // Method 5: Reset canvas size to ensure clean state
                const { width, height } = canvas.getBoundingClientRect();
                canvas.width = width * window.devicePixelRatio;
                canvas.height = height * window.devicePixelRatio;
                ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
                canvas.style.width = width + 'px';
                canvas.style.height = height + 'px';
                
                // Create a safe configuration that handles potential plugin issues
                const safeConfig = {
                    ...config,
                    options: {
                        ...config.options,
                        // Add comprehensive plugin handling
                        plugins: {
                            legend: {
                                display: true,
                                position: 'top',
                                labels: {
                                    usePointStyle: true,
                                    padding: 15,
                                    font: {
                                        size: 12
                                    },
                                    generateLabels: function(chart) {
                                        try {
                                            return Chart.defaults.plugins.legend.labels.generateLabels(chart);
                                        } catch (error) {
                                            console.error('Legend generation error:', error);
                                            return [];
                                        }
                                    }
                                }
                            },
                            tooltip: {
                                enabled: true,
                                mode: 'index',
                                intersect: false,
                                callbacks: {
                                    label: function(context) {
                                        try {
                                            let label = context.dataset.label || '';
                                            if (label) {
                                                label += ': ';
                                            }
                                            if (context.parsed.y !== null) {
                                                label += new Intl.NumberFormat('en-US').format(context.parsed.y);
                                            }
                                            return label;
                                        } catch (error) {
                                            console.error('Tooltip callback error:', error);
                                            return 'Data';
                                        }
                                    }
                                }
                            },
                            ...config.options?.plugins
                        },
                        // Add animation configuration to prevent race conditions
                        animation: {
                            duration: 300,
                            easing: 'easeInOutQuart',
                            onComplete: function() {
                                console.log(`Admin Dashboard: Chart animation completed for ${canvasId}`);
                            },
                            onProgress: function(animation) {
                                // Don't log progress to avoid spam
                            }
                        },
                        // Error handling for interactions
                        onHover: function(event, activeElements) {
                            try {
                                // Safe hover handling
                                if (activeElements && activeElements.length > 0) {
                                    canvas.style.cursor = 'pointer';
                                } else {
                                    canvas.style.cursor = 'default';
                                }
                            } catch (error) {
                                console.error('Chart hover error:', error);
                            }
                        }
                    }
                };
                
                // Create the chart with try-catch for initialization errors
                let chart;
                try {
                    chart = new Chart(ctx, safeConfig);
                    console.log(`Admin Dashboard: Successfully created chart on canvas ${canvasId}`);
                } catch (chartError) {
                    // If chart creation still fails, try with minimal config
                    console.error(`Admin Dashboard: Chart creation failed with full config, trying minimal config:`, chartError);
                    
                    const minimalConfig = {
                        type: config.type,
                        data: config.data,
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: { display: false }
                            }
                        }
                    };
                    
                    chart = new Chart(ctx, minimalConfig);
                    console.log(`Admin Dashboard: Chart created with minimal config on canvas ${canvasId}`);
                }
                
                // Store reference on canvas for debugging
                canvas.chartInstance = chart;
                
                return chart;
                
            } catch (error) {
                console.error('Admin Dashboard: Chart creation failed completely:', error);
                this.handleError(`Chart initialization failed: ${error.message}`);
                
                // Attempt to clean up canvas on failure
                try {
                    if (canvas && canvas.getContext) {
                        const ctx = canvas.getContext('2d');
                        ctx.clearRect(0, 0, canvas.width, canvas.height);
                        // Remove any Chart.js references
                        canvas.removeAttribute('data-chartjs-id');
                        delete canvas.chartInstance;
                    }
                } catch (cleanupError) {
                    console.error('Admin Dashboard: Canvas cleanup failed:', cleanupError);
                }
                
                return null;
            }
        },

        // Get common chart options
        getChartOptions(isCurrency = false) {
            return {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 15,
                            font: {
                                size: 12
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            font: {
                                size: 11
                            },
                            callback: function(value) {
                                const num = Number(value);
                                if (isNaN(num)) return value;
                                return isCurrency ? 
                                    '$' + num.toLocaleString() : 
                                    num.toLocaleString();
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: {
                                size: 11
                            }
                        }
                    }
                },
                interaction: {
                    mode: 'index',
                    intersect: false
                }
            };
        },

        // Update chart data
        updateChart(chartName, data) {
            const chart = this.charts?.[chartName];
            if (!chart || !data) return;

            try {
                chart.data.labels = data.labels || [];
                chart.data.datasets[0].data = data.values || [];
                chart.update('none');
                console.log(`Admin Dashboard: ${chartName} chart updated`);
            } catch (error) {
                console.error(`Admin Dashboard: Failed to update ${chartName} chart:`, error);
            }
        },

        // Toggle auto refresh
        toggleAutoRefresh() {
            this.autoRefresh = !this.autoRefresh;

            if (this.autoRefresh) {
                this.setupAutoRefresh();
            } else {
                if (this.refreshInterval) {
                    clearInterval(this.refreshInterval);
                    this.refreshInterval = null;
                }
            }
        },

        // Cleanup when component is destroyed
        destroy() {
            if (this.refreshInterval) {
                clearInterval(this.refreshInterval);
            }
        }
    }
}

// Export for use in modules if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { adminDashboard };
}

// Define Alpine.js component properly - ensure Alpine is available
document.addEventListener('alpine:init', () => {
    if (window.Alpine) {
        Alpine.data('adminDashboard', adminDashboard);

        // Global Alpine stores that were in the inline component
        Alpine.store('notifications', {
            items: [],
            add(notification) {
                this.items.push({
                    id: Date.now(),
                    ...notification
                });
                setTimeout(() => this.remove(notification.id), 5000);
            },
            remove(id) {
                this.items = this.items.filter(item => item.id !== id);
            }
        });

        Alpine.store('taskCount', 0);
        console.log('Alpine.js adminDashboard component registered successfully');
    } else {
        console.error('Alpine.js not available during initialization');
    }
});

// Fallback for Alpine.js not ready
document.addEventListener('DOMContentLoaded', () => {
    // Wait for Alpine to be available with a timeout
    let attempts = 0;
    const maxAttempts = 20; // 2 seconds max

    const registerAlpine = () => {
        if (window.Alpine && !window.Alpine.data('adminDashboard')) {
            try {
                Alpine.data('adminDashboard', adminDashboard);
                console.log('Alpine.js adminDashboard component registered via fallback');
            } catch (error) {
                console.warn('Failed to register Alpine component:', error);
            }
        } else if (attempts < maxAttempts) {
            attempts++;
            setTimeout(registerAlpine, 100);
        } else {
            console.error('Alpine.js not available after timeout - component may not work');
        }
    };

    setTimeout(registerAlpine, 100);
});

// Also keep global function for backward compatibility
window.adminDashboard = adminDashboard;

// Debug: Ensure function is available
document.addEventListener('DOMContentLoaded', function() {
    console.log('Admin.js loaded, adminDashboard available:', typeof adminDashboard === 'function');
    if (typeof Alpine !== 'undefined') {
        console.log('Alpine.js is available');
    } else {
        console.log('Alpine.js not yet available, will be loaded with defer');
    }
});

// Debug: When Alpine starts
document.addEventListener('alpine:init', () => {
    console.log('Alpine.js initialized');
});

// Initialize any global dashboard functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log('Admin Dashboard JS loaded successfully');
});
