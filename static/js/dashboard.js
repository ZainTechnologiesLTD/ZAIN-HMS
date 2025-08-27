/**
 * ZAIN HMS - Dashboard Module JavaScript
 * Enhanced functionality for dashboard widgets and real-time updates
 */

// Dashboard Manager - Alpine.js component
function dashboardManager() {
    return {
        loading: false,
        realTimeUpdates: true,
        refreshInterval: null,
        
        init() {
            this.initializeCharts();
            this.startRealTimeUpdates();
            this.initializeWidgets();
        },
        
        initializeCharts() {
            // Patient Flow Chart
            if (document.getElementById('patientFlowChart')) {
                this.setupPatientFlowChart();
            }
            
            // Revenue Chart
            if (document.getElementById('revenueChart')) {
                this.setupRevenueChart();
            }
            
            // Appointments Chart
            if (document.getElementById('appointmentsChart')) {
                this.setupAppointmentsChart();
            }
            
            // Bed Occupancy Chart
            if (document.getElementById('occupancyChart')) {
                this.setupOccupancyChart();
            }
        },
        
        setupPatientFlowChart() {
            const ctx = document.getElementById('patientFlowChart').getContext('2d');
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['OPD', 'IPD', 'Emergency', 'Discharged'],
                    datasets: [{
                        data: [45, 25, 15, 35],
                        backgroundColor: [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(34, 197, 94, 0.8)',
                            'rgba(239, 68, 68, 0.8)',
                            'rgba(156, 163, 175, 0.8)'
                        ],
                        borderWidth: 2,
                        borderColor: '#fff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        },
        
        setupRevenueChart() {
            const ctx = document.getElementById('revenueChart').getContext('2d');
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                    datasets: [{
                        label: 'Revenue',
                        data: [12000, 19000, 15000, 25000, 22000, 30000],
                        borderColor: 'rgb(59, 130, 246)',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
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
        
        setupAppointmentsChart() {
            const ctx = document.getElementById('appointmentsChart').getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    datasets: [{
                        label: 'Appointments',
                        data: [65, 59, 80, 81, 56, 45, 25],
                        backgroundColor: 'rgba(34, 197, 94, 0.8)',
                        borderColor: 'rgba(34, 197, 94, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        },
        
        setupOccupancyChart() {
            const ctx = document.getElementById('occupancyChart').getContext('2d');
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Occupied', 'Available'],
                    datasets: [{
                        data: [75, 25],
                        backgroundColor: [
                            'rgba(245, 158, 11, 0.8)',
                            'rgba(156, 163, 175, 0.3)'
                        ],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '70%',
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
        },
        
        initializeWidgets() {
            // Initialize progress bars
            this.animateProgressBars();
            
            // Initialize counters
            this.animateCounters();
            
            // Initialize tooltips
            this.initializeTooltips();
        },
        
        animateProgressBars() {
            const progressBars = document.querySelectorAll('.progress-fill');
            progressBars.forEach(bar => {
                const width = bar.dataset.width || bar.style.width;
                bar.style.width = '0%';
                setTimeout(() => {
                    bar.style.width = width;
                }, 500);
            });
        },
        
        animateCounters() {
            const counters = document.querySelectorAll('.stat-number');
            counters.forEach(counter => {
                const target = parseInt(counter.textContent.replace(/[^0-9]/g, ''));
                const duration = 2000;
                const step = target / (duration / 16);
                let current = 0;
                
                const timer = setInterval(() => {
                    current += step;
                    if (current >= target) {
                        counter.textContent = target.toLocaleString();
                        clearInterval(timer);
                    } else {
                        counter.textContent = Math.floor(current).toLocaleString();
                    }
                }, 16);
            });
        },
        
        initializeTooltips() {
            if (typeof bootstrap !== 'undefined') {
                const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
                const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
                    return new bootstrap.Tooltip(tooltipTriggerEl);
                });
            }
        },
        
        startRealTimeUpdates() {
            if (this.realTimeUpdates) {
                this.refreshInterval = setInterval(() => {
                    this.updateDashboardData();
                }, 30000); // Update every 30 seconds
            }
        },
        
        stopRealTimeUpdates() {
            if (this.refreshInterval) {
                clearInterval(this.refreshInterval);
                this.refreshInterval = null;
            }
        },
        
        toggleRealTimeUpdates() {
            this.realTimeUpdates = !this.realTimeUpdates;
            if (this.realTimeUpdates) {
                this.startRealTimeUpdates();
                showNotification('Real-time updates enabled', 'success');
            } else {
                this.stopRealTimeUpdates();
                showNotification('Real-time updates disabled', 'info');
            }
        },
        
        updateDashboardData() {
            if (!this.realTimeUpdates) return;
            
            fetch('/dashboard/api/stats/', {
                method: 'GET',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                }
            })
            .then(response => response.json())
            .then(data => {
                this.updateStatsCards(data.stats);
                this.updateActivity(data.activities);
                this.updateAlerts(data.alerts);
            })
            .catch(error => {
                console.error('Failed to update dashboard data:', error);
            });
        },
        
        updateStatsCards(stats) {
            Object.keys(stats).forEach(key => {
                const element = document.querySelector(`[data-stat="${key}"]`);
                if (element) {
                    element.textContent = stats[key];
                }
            });
        },
        
        updateActivity(activities) {
            const container = document.querySelector('.activity-list');
            if (container && activities.length > 0) {
                // Update activity list with new items
                const activityHTML = activities.map(activity => `
                    <div class="activity-item">
                        <div class="activity-icon ${activity.type}">
                            <i class="fas fa-${activity.icon}"></i>
                        </div>
                        <div class="activity-content">
                            <div class="activity-title">${activity.title}</div>
                            <div class="activity-description">${activity.description}</div>
                            <div class="activity-time">${activity.time}</div>
                        </div>
                    </div>
                `).join('');
                
                container.innerHTML = activityHTML;
            }
        },
        
        updateAlerts(alerts) {
            const container = document.querySelector('.dashboard-alerts');
            if (container && alerts.length > 0) {
                alerts.forEach(alert => {
                    if (!document.querySelector(`[data-alert-id="${alert.id}"]`)) {
                        this.addAlert(alert);
                    }
                });
            }
        },
        
        addAlert(alert) {
            const alertHTML = `
                <div class="dashboard-alert ${alert.type}" data-alert-id="${alert.id}">
                    <div class="alert-header">
                        <div class="alert-icon ${alert.type}">
                            <i class="fas fa-${alert.icon}"></i>
                        </div>
                        <h6 class="alert-title">${alert.title}</h6>
                    </div>
                    <p class="alert-description">${alert.description}</p>
                    <div class="alert-actions">
                        <button class="btn btn-sm btn-primary" onclick="handleAlert('${alert.id}', 'acknowledge')">
                            Acknowledge
                        </button>
                        <button class="btn btn-sm btn-outline-secondary" onclick="dismissAlert('${alert.id}')">
                            Dismiss
                        </button>
                    </div>
                </div>
            `;
            
            const container = document.querySelector('.dashboard-alerts');
            if (container) {
                container.insertAdjacentHTML('afterbegin', alertHTML);
            }
        },
        
        refreshDashboard() {
            this.loading = true;
            
            // Refresh all dashboard data
            Promise.all([
                this.updateDashboardData(),
                this.refreshCharts()
            ]).then(() => {
                this.loading = false;
                showNotification('Dashboard refreshed successfully', 'success');
            }).catch(error => {
                this.loading = false;
                showNotification('Failed to refresh dashboard', 'error');
                console.error('Dashboard refresh error:', error);
            });
        },
        
        refreshCharts() {
            // Re-initialize all charts with fresh data
            return fetch('/dashboard/api/charts/', {
                method: 'GET',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                }
            })
            .then(response => response.json())
            .then(data => {
                // Update chart data
                Chart.helpers.each(Chart.instances, function(instance) {
                    if (data[instance.canvas.id]) {
                        instance.data = data[instance.canvas.id];
                        instance.update();
                    }
                });
            });
        }
    }
}

// Alert Management Functions
function handleAlert(alertId, action) {
    fetch(`/dashboard/api/alerts/${alertId}/${action}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(`Alert ${action}d successfully`, 'success');
            if (action === 'acknowledge') {
                const alertElement = document.querySelector(`[data-alert-id="${alertId}"]`);
                if (alertElement) {
                    alertElement.style.opacity = '0.6';
                }
            }
        }
    })
    .catch(error => {
        showNotification('Failed to handle alert', 'error');
        console.error('Alert handling error:', error);
    });
}

function dismissAlert(alertId) {
    const alertElement = document.querySelector(`[data-alert-id="${alertId}"]`);
    if (alertElement) {
        alertElement.style.opacity = '0';
        setTimeout(() => {
            alertElement.remove();
        }, 300);
    }
    
    fetch(`/dashboard/api/alerts/${alertId}/dismiss/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
        }
    })
    .catch(error => {
        console.error('Alert dismissal error:', error);
    });
}

// Quick Action Functions
function quickAddPatient() {
    window.location.href = '/patients/add/';
}

function quickAddAppointment() {
    window.location.href = '/appointments/add/';
}

function quickViewReports() {
    window.location.href = '/reports/';
}

function quickManageInventory() {
    window.location.href = '/inventory/';
}

// Utility Functions
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts if Chart.js is available
    if (typeof Chart !== 'undefined') {
        Chart.defaults.font.family = "'Inter', sans-serif";
        Chart.defaults.color = '#6B7280';
    }
    
    // Initialize other dashboard features
    const dashboard = dashboardManager();
    if (dashboard) {
        dashboard.init();
    }
});

// Export functions for global access
window.dashboardManager = dashboardManager;
window.handleAlert = handleAlert;
window.dismissAlert = dismissAlert;
window.quickAddPatient = quickAddPatient;
window.quickAddAppointment = quickAddAppointment;
window.quickViewReports = quickViewReports;
window.quickManageInventory = quickManageInventory;
