// Analytics Dashboard JavaScript
// Pure JavaScript without Django template syntax

class AnalyticsDashboard {
    constructor() {
        this.trendsChart = null;
        this.departmentChart = null;
        this.init();
    }

    init() {
        document.addEventListener('DOMContentLoaded', () => {
            this.initTrendsChart();
            this.initDepartmentChart();
            this.setupAutoRefresh();
        });
    }

    initTrendsChart() {
        const trendsCtx = document.getElementById('trendsChart');
        if (!trendsCtx) return;

        // Data will be provided via window.analyticsData
        const trendsData = window.analyticsData?.appointmentTrends || [];

        this.trendsChart = new Chart(trendsCtx.getContext('2d'), {
            type: 'line',
            data: {
                labels: trendsData.map(item => item.month),
                datasets: [{
                    label: 'Appointments',
                    data: trendsData.map(item => item.count),
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.1)',
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
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    initDepartmentChart() {
        const deptCtx = document.getElementById('departmentChart');
        if (!deptCtx) return;

        // Data will be provided via window.analyticsData
        const departmentData = window.analyticsData?.departmentStats || [];

        this.departmentChart = new Chart(deptCtx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: departmentData.map(item => item.department__name || 'General'),
                datasets: [{
                    data: departmentData.map(item => item.count),
                    backgroundColor: [
                        '#FF6384',
                        '#36A2EB',
                        '#FFCE56',
                        '#4BC0C0',
                        '#9966FF',
                        '#FF9F40'
                    ],
                    borderWidth: 0
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
                            usePointStyle: true
                        }
                    }
                }
            }
        });
    }

    setupAutoRefresh() {
        // Auto refresh data every 5 minutes
        setInterval(() => {
            fetch(window.location.href + '?ajax=1')
                .then(response => response.json())
                .then(data => {
                    if (data.updated) {
                        location.reload();
                    }
                })
                .catch(error => {
                    console.error('Error refreshing analytics data:', error);
                });
        }, 300000); // 5 minutes
    }

    updateCharts(newData) {
        if (this.trendsChart && newData.appointmentTrends) {
            this.trendsChart.data.labels = newData.appointmentTrends.map(item => item.month);
            this.trendsChart.data.datasets[0].data = newData.appointmentTrends.map(item => item.count);
            this.trendsChart.update();
        }

        if (this.departmentChart && newData.departmentStats) {
            this.departmentChart.data.labels = newData.departmentStats.map(item => item.department__name || 'General');
            this.departmentChart.data.datasets[0].data = newData.departmentStats.map(item => item.count);
            this.departmentChart.update();
        }
    }
}

// Initialize dashboard
new AnalyticsDashboard();
