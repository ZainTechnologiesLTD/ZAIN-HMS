/**
 * ZAIN HMS - Reports Module JavaScript
 * Enhanced functionality for reports and analytics
 */

// Reports Manager - Alpine.js component
function reportsManager() {
    return {
        loading: false,
        filters: {
            dateFrom: '',
            dateTo: '',
            department: '',
            reportType: '',
            doctor: ''
        },
        
        init() {
            this.setupChart();
            this.setDefaultDates();
        },
        
        setDefaultDates() {
            const today = new Date();
            const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, today.getDate());
            
            this.filters.dateTo = today.toISOString().split('T')[0];
            this.filters.dateFrom = lastMonth.toISOString().split('T')[0];
        },
        
        setupChart() {
            const ctx = document.getElementById('revenueChart').getContext('2d');
            
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                    datasets: [{
                        label: 'Revenue ($)',
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
        
        applyFilters() {
            this.loading = true;
            
            // Simulate API call
            setTimeout(() => {
                this.loading = false;
                showNotification('Filters applied successfully', 'success');
                // Refresh data here
            }, 1000);
        },
        
        resetFilters() {
            this.filters = {
                dateFrom: '',
                dateTo: '',
                department: '',
                reportType: '',
                doctor: ''
            };
            this.setDefaultDates();
            showNotification('Filters reset', 'info');
        }
    }
}

// Report Generation Functions
function generateReport(type) {
    showLoading();
    
    fetch(`/reports/api/generate/${type}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            filters: getActiveFilters()
        })
    })
    .then(response => response.blob())
    .then(blob => {
        hideLoading();
        downloadBlob(blob, `${type}_report_${new Date().toISOString().split('T')[0]}.pdf`);
        showNotification('Report generated successfully!', 'success');
    })
    .catch(error => {
        hideLoading();
        showNotification('Failed to generate report', 'error');
        console.error('Report generation error:', error);
    });
}

function exportReport(type, format) {
    showLoading();
    
    const url = `/reports/api/export/${type}/${format}/`;
    
    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
        }
    })
    .then(response => response.blob())
    .then(blob => {
        hideLoading();
        downloadBlob(blob, `${type}_report.${format}`);
        showNotification(`${format.toUpperCase()} report exported successfully!`, 'success');
    })
    .catch(error => {
        hideLoading();
        showNotification('Export failed', 'error');
        console.error('Export error:', error);
    });
}

function refreshData() {
    showLoading();
    
    // Refresh all data
    setTimeout(() => {
        hideLoading();
        showNotification('Data refreshed successfully', 'success');
        location.reload();
    }, 1500);
}

// Report Management Functions
function shareReport(reportId) {
    const shareUrl = `${window.location.origin}/reports/share/${reportId}/`;
    
    if (navigator.share) {
        navigator.share({
            title: 'Hospital Report',
            url: shareUrl
        });
    } else {
        // Fallback - copy to clipboard
        navigator.clipboard.writeText(shareUrl).then(() => {
            showNotification('Share link copied to clipboard', 'success');
        }).catch(() => {
            // Manual fallback
            const textArea = document.createElement('textarea');
            textArea.value = shareUrl;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            showNotification('Share link copied to clipboard', 'success');
        });
    }
}

function deleteReport(reportId) {
    if (confirm('Are you sure you want to delete this report?')) {
        fetch(`/reports/api/delete/${reportId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Report deleted successfully', 'success');
                location.reload();
            } else {
                showNotification('Failed to delete report', 'error');
            }
        })
        .catch(error => {
            showNotification('Failed to delete report', 'error');
            console.error('Delete error:', error);
        });
    }
}

function scheduleReport() {
    // Open scheduling modal
    showNotification('Report scheduling feature coming soon!', 'info');
}

// Utility Functions
function getActiveFilters() {
    const form = document.querySelector('.filters-grid');
    const formData = new FormData(form);
    const filters = {};
    
    for (let [key, value] of formData.entries()) {
        if (value) filters[key] = value;
    }
    
    return filters;
}

function downloadBlob(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

function showLoading() {
    const component = document.querySelector('[x-data]');
    if (component && component.__x) {
        component.__x.$data.loading = true;
    }
}

function hideLoading() {
    const component = document.querySelector('[x-data]');
    if (component && component.__x) {
        component.__x.$data.loading = false;
    }
}

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
    // Auto-refresh data every 5 minutes
    setInterval(refreshData, 300000);
    
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
});

// Export functions for global access
window.reportsManager = reportsManager;
window.generateReport = generateReport;
window.exportReport = exportReport;
window.refreshData = refreshData;
window.shareReport = shareReport;
window.deleteReport = deleteReport;
window.scheduleReport = scheduleReport;
