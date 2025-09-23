// Analytics Dashboard JavaScript
// Note: This file contains Django template syntax and should be processed server-side

// Trends Chart
document.addEventListener('DOMContentLoaded', function() {
    const trendsCtx = document.getElementById('trendsChart');
    if (trendsCtx) {
        const trendsChart = new Chart(trendsCtx.getContext('2d'), {
            type: 'line',
            data: {
                labels: {{ appointment_trends|safe }}.map(item => item.month),
                datasets: [{
                    label: 'Appointments',
                    data: {{ appointment_trends|safe }}.map(item => item.count),
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

// Department Chart
const deptCtx = document.getElementById('departmentChart').getContext('2d');
const departmentChart = new Chart(deptCtx, {
    type: 'doughnut',
    data: {
        labels: {{ department_stats|safe }}.map(item => item.department__name || 'General'),
        datasets: [{
            data: {{ department_stats|safe }}.map(item => item.count),
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

// Auto refresh data every 5 minutes
setInterval(function() {
    fetch(window.location.href + '?ajax=1')
    .then(response => response.json())
    .then(data => {
        // Update charts with new data
        if (data.updated) {
            location.reload();
        }
    })
    .catch(error => console.log('Auto-refresh failed:', error));
}, 300000); // 5 minutes
