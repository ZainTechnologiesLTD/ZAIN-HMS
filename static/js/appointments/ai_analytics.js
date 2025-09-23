document.addEventListener('DOMContentLoaded', function() {
    {% if ai_insights_available and analytics_data %}
    // Efficiency Trends Chart
    const efficiencyCtx = document.getElementById('efficiencyChart');
    if (efficiencyCtx) {
        new Chart(efficiencyCtx, {
            type: 'line',
            data: {
                labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
                datasets: [{
                    label: 'Efficiency %',
                    data: {{ analytics_data.efficiency_trends.weekly_efficiency|default:"[85, 87, 89, 91]" }},
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
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
                        beginAtZero: false,
                        min: 80,
                        max: 100
                    }
                }
            }
        });
    }

    // Utilization Patterns Chart
    const utilizationCtx = document.getElementById('utilizationChart');
    if (utilizationCtx) {
        new Chart(utilizationCtx, {
            type: 'bar',
            data: {
                labels: ['8AM', '9AM', '10AM', '11AM', '12PM', '1PM', '2PM', '3PM', '4PM', '5PM'],
                datasets: [{
                    label: 'Appointments',
                    data: [12, 19, 15, 8, 10, 16, 18, 14, 11, 9],
                    backgroundColor: 'rgba(102, 126, 234, 0.6)',
                    borderColor: '#667eea',
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
    }
    {% endif %}
});

function exportAnalytics(format) {
    // Implement analytics export functionality
    console.log(`Exporting analytics in ${format} format`);
    // This would typically make an AJAX call to export endpoint
}

function refreshAnalytics() {
    // Refresh analytics data
    window.location.reload();
}
