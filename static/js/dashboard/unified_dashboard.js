/**
 * Unified Dashboard JavaScript - ZAIN HMS
 * Reports Manager for Alpine.js
 */

// Reports Manager function for Alpine.js
function reportsManager() {
    return {
        // Data properties
        loading: false,
        filters: {
            dateFrom: '',
            dateTo: '',
            department: '',
            reportType: '',
            doctor: ''
        },
        quickStats: {
            revenue: 0,
            patients: 0,
            appointments: 0,
            occupancy: 0
        },
        
        // Initialization
        init() {
            console.log('Reports Manager initialized');
            this.loadInitialData();
            this.setupDatePickers();
        },
        
        // Load initial dashboard data
        loadInitialData() {
            this.loadQuickStats();
            this.loadChartData();
        },
        
        // Setup date pickers
        setupDatePickers() {
            // Set default date range (last 30 days)
            const today = new Date();
            const thirtyDaysAgo = new Date(today);
            thirtyDaysAgo.setDate(today.getDate() - 30);
            
            this.filters.dateFrom = thirtyDaysAgo.toISOString().split('T')[0];
            this.filters.dateTo = today.toISOString().split('T')[0];
        },
        
        // Load quick statistics
        loadQuickStats() {
            // Placeholder - in real implementation, this would fetch from API
            this.quickStats = {
                revenue: 45250.00,
                patients: 234,
                appointments: 156,
                occupancy: 78
            };
            
            // Update DOM elements if they exist
            this.updateQuickStatElements();
        },
        
        // Update quick stat elements in DOM
        updateQuickStatElements() {
            const revenueEl = document.querySelector('.quick-stat-number.revenue');
            const patientsEl = document.querySelector('.quick-stat-number.patients');
            const appointmentsEl = document.querySelector('.quick-stat-number.appointments');
            const occupancyEl = document.querySelector('.quick-stat-number.occupancy');
            
            if (revenueEl) revenueEl.textContent = `$${this.quickStats.revenue.toLocaleString()}`;
            if (patientsEl) patientsEl.textContent = this.quickStats.patients.toLocaleString();
            if (appointmentsEl) appointmentsEl.textContent = this.quickStats.appointments.toLocaleString();
            if (occupancyEl) occupancyEl.textContent = `${this.quickStats.occupancy}%`;
        },
        
        // Load chart data
        loadChartData() {
            // Only initialize charts if Chart.js is available and canvas exists
            if (typeof Chart !== 'undefined') {
                // Check if revenueChart canvas exists and isn't already used by financial_dashboard.js
                const chartCanvas = document.getElementById('revenueChart');
                if (chartCanvas && !window.revenueChart) {
                    this.initializeRevenueChart();
                }
            }
        },
        
        // Initialize revenue chart
        initializeRevenueChart() {
            const ctx = document.getElementById('revenueChart');
            if (!ctx) return;
            
            // Check if a chart already exists and destroy it
            if (window.revenueChart instanceof Chart) {
                window.revenueChart.destroy();
            }
            
            // Sample data - replace with real data
            const data = {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'Revenue',
                    data: [12000, 19000, 15000, 25000, 22000, 30000],
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.1
                }]
            };
            
            window.revenueChart = new Chart(ctx, {
                type: 'line',
                data: data,
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Revenue Trends'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return '$' + value.toLocaleString();
                                }
                            }
                        }
                    }
                }
            });
        },
        
        // Apply filters
        applyFilters() {
            this.loading = true;
            
            // Simulate API call
            setTimeout(() => {
                console.log('Filters applied:', this.filters);
                this.loadQuickStats();
                this.loadChartData();
                this.loading = false;
            }, 1000);
        },
        
        // Reset filters
        resetFilters() {
            this.filters = {
                dateFrom: '',
                dateTo: '',
                department: '',
                reportType: '',
                doctor: ''
            };
            this.setupDatePickers();
            this.applyFilters();
        }
    };
}

// Global utility functions
function refreshData() {
    if (typeof Alpine !== 'undefined' && Alpine.store) {
        // If using Alpine stores
        const reportsStore = Alpine.store('reports');
        if (reportsStore && reportsStore.loadInitialData) {
            reportsStore.loadInitialData();
        }
    } else {
        // Fallback - reload the page
        window.location.reload();
    }
}

function exportReport(type, format) {
    console.log(`Exporting ${type} report as ${format}`);
    
    // Create a temporary link for download
    const link = document.createElement('a');
    link.href = `/en/reports/export/${type}/?format=${format}`;
    link.download = `${type}_report.${format}`;
    
    // Trigger download
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function generateReport(type) {
    console.log(`Generating ${type} report`);
    
    // Redirect to report generation page
    window.location.href = `/en/reports/generate/${type}/`;
}

function scheduleReport() {
    console.log('Opening report scheduling dialog');
    
    // This would open a modal for scheduling reports
    alert('Report scheduling feature coming soon!');
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Unified Dashboard JS loaded');
    
    // Initialize any global functionality
    if (typeof initializeGlobalFeatures === 'function') {
        initializeGlobalFeatures();
    }
});