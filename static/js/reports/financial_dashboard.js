let revenueChart = null;
let currentPeriod = '30days';

document.addEventListener('DOMContentLoaded', function() {
    initializeChart();  // Initialize chart first
    
    // Add a small delay to ensure chart is fully initialized
    setTimeout(() => {
        loadFinancialData();
        loadRecentTransactions();
    }, 100);
});

async function loadFinancialData() {
    try {
        // Temporary test data to verify frontend functionality
        const testData = {
            daily_revenue: [
                { date: '2025-09-22', revenue: 1500.50 },
                { date: '2025-09-21', revenue: 2200.75 },
                { date: '2025-09-20', revenue: 1800.25 },
                { date: '2025-09-19', revenue: 2450.00 },
                { date: '2025-09-18', revenue: 1950.80 }
            ],
            total_revenue: 10001.30,
            average_daily: 2000.26,
            pending_bills: 1250.75
        };

        updateSummaryCards(testData);
        updateChart(testData.daily_revenue);
        hideNoDataMessage();
        
        // Uncomment this section when backend is ready:
        // const response = await fetch('/en/reports/quick/financial/');
        // const data = await response.json();
        // if (response.ok) {
        //     updateSummaryCards(data);
        //     updateChart(data.daily_revenue);
        //     if (data.daily_revenue.length === 0 || data.total_revenue === 0) {
        //         showNoDataMessage();
        //     } else {
        //         hideNoDataMessage();
        //     }
        // } else {
        //     console.error('Error loading financial data:', data.error);
        //     showNoDataMessage();
        // }
    } catch (error) {
        console.error('Failed to load financial data:', error);
        showNoDataMessage();
    }
}

function updateSummaryCards(data) {
    const totalRevenueEl = document.getElementById('total-revenue');
    const averageDailyEl = document.getElementById('average-daily');
    const pendingBillsEl = document.getElementById('pending-bills');
    
    if (totalRevenueEl) totalRevenueEl.textContent = '$' + data.total_revenue.toFixed(2);
    if (averageDailyEl) averageDailyEl.textContent = '$' + data.average_daily.toFixed(2);
    if (pendingBillsEl) pendingBillsEl.textContent = '$' + data.pending_bills.toFixed(2);
}

function initializeChart() {
    const chartCanvas = document.getElementById('revenueChart');
    if (!chartCanvas) {
        console.warn('Revenue chart canvas not found');
        return;
    }
    
    // Destroy existing chart if it exists
    if (window.revenueChart instanceof Chart) {
        console.log('Destroying existing chart');
        window.revenueChart.destroy();
    }
    
    const ctx = chartCanvas.getContext('2d');

    console.log('Initializing new chart');
    window.revenueChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Daily Revenue',
                data: [],
                borderColor: '#053377',
                backgroundColor: 'rgba(5, 51, 119, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#053377',
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2,
                pointRadius: 6,
                pointHoverRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: '#053377',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    borderColor: '#053377',
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            return 'Revenue: $' + context.parsed.y.toFixed(2);
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: '#6c757d',
                        font: {
                            size: 12
                        }
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0,0,0,0.1)'
                    },
                    ticks: {
                        color: '#6c757d',
                        font: {
                            size: 12
                        },
                        callback: function(value) {
                            return '$' + value.toFixed(0);
                        }
                    }
                }
            }
        }
    });
    
    console.log('Chart initialized successfully:', window.revenueChart);
}

function updateChart(dailyRevenue) {
    if (!window.revenueChart || !dailyRevenue || dailyRevenue.length === 0) {
        console.warn('Chart or data not available for update');
        return;
    }

    // Check if chart data structure exists
    if (!window.revenueChart.data || !window.revenueChart.data.datasets || !window.revenueChart.data.datasets[0]) {
        console.warn('Chart data structure not properly initialized');
        return;
    }

    const labels = dailyRevenue.reverse().map(item => {
        const date = new Date(item.date);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });

    const data = dailyRevenue.map(item => item.revenue);

    window.revenueChart.data.labels = labels;
    window.revenueChart.data.datasets[0].data = data;
    window.revenueChart.update();
}

async function loadRecentTransactions() {
    try {
        // This would need to be implemented to fetch recent billing transactions
        // For now, show a placeholder message
        const transactionsBody = document.getElementById('transactions-body');
        if (transactionsBody) {
            transactionsBody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center py-4 text-muted">
                        <i class="bi bi-info-circle me-2"></i>
    Recent transactions will be displayed here when billing data is available.
                    </td>
                </tr>
            `;
        }
    } catch (error) {
        console.error('Failed to load recent transactions:', error);
    }
}

function changePeriod(period) {
    // Update active button
    document.querySelectorAll('.period-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');

    currentPeriod = period;

    // Show loading
    document.getElementById('chart-loading').style.display = 'block';

    // In a real implementation, this would fetch data for the selected period
    setTimeout(() => {
        document.getElementById('chart-loading').style.display = 'none';
        // loadFinancialData(period);
    }, 1000);
}

function exportFinancialReport(format) {
    const exportBtn = event.target.closest('.export-btn');
    const originalText = exportBtn.innerHTML;

    exportBtn.innerHTML = '<div class="spinner-border spinner-border-sm me-2" role="status"></div>Exporting...';
    exportBtn.disabled = true;

    // Simulate export process
    setTimeout(() => {
        exportBtn.innerHTML = originalText;
        exportBtn.disabled = false;

        // In a real implementation, this would trigger the actual export
        alert(`Financial report exported as ${format.toUpperCase()}!`);
    }, 2000);
}

function showNoDataMessage() {
    const noDataEl = document.getElementById('no-data');
    const chartEl = document.getElementById('revenueChart');
    const loadingEl = document.getElementById('chart-loading');
    
    if (noDataEl) noDataEl.style.display = 'block';
    if (chartEl) chartEl.style.display = 'none';
    if (loadingEl) loadingEl.style.display = 'none';
}

function hideNoDataMessage() {
    const noDataEl = document.getElementById('no-data');
    const chartEl = document.getElementById('revenueChart');
    const loadingEl = document.getElementById('chart-loading');
    
    if (noDataEl) noDataEl.style.display = 'none';
    if (chartEl) chartEl.style.display = 'block';
    if (loadingEl) loadingEl.style.display = 'none';
}

// Auto-refresh data every 5 minutes
setInterval(loadFinancialData, 5 * 60 * 1000);
