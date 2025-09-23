// CSRF token
const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;

// Initialize payment chart
document.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('paymentChart').getContext('2d');

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Cash', 'Card', 'Mobile Money'],
            datasets: [{
                data: [
                    {{ today_summary.cash_sales }},
                    {{ today_summary.card_sales }},
                    {{ today_summary.mobile_sales }}
                ],
                backgroundColor: [
                    '#28a745',
                    '#007bff',
                    '#ffc107'
                ],
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
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

    // Initialize cash counting
    initializeCashCount();
});

function initializeCashCount() {
    const denominationInputs = document.querySelectorAll('.denomination-input');

    denominationInputs.forEach(input => {
        input.addEventListener('input', calculateCashTotal);
    });
}

function calculateCashTotal() {
    let total = 0;
    const denominationInputs = document.querySelectorAll('.denomination-input');

    denominationInputs.forEach(input => {
        const count = parseInt(input.value) || 0;
        const value = parseFloat(input.dataset.value);
        const amount = count * value;

        // Update the amount column for this row
        const amountCell = input.closest('tr').querySelector('.amount');
        amountCell.textContent = '$' + amount.toFixed(2);

        total += amount;
    });

    // Update total
    document.getElementById('total-cash-counted').textContent = '$' + total.toFixed(2);
    document.getElementById('actual-cash').textContent = '$' + total.toFixed(2);

    // Calculate variance
    const expectedCash = {{ today_summary.cash_sales }};
    const variance = total - expectedCash;
    const varianceElement = document.getElementById('cash-variance-amount');
    const statusElement = document.getElementById('variance-status');

    varianceElement.textContent = '$' + Math.abs(variance).toFixed(2);

    if (variance > 0) {
        varianceElement.className = 'fs-4 text-success';
        statusElement.innerHTML = '<i class="fas fa-arrow-up text-success"></i> Over';
    } else if (variance < 0) {
        varianceElement.className = 'fs-4 text-danger';
        statusElement.innerHTML = '<i class="fas fa-arrow-down text-danger"></i> Short';
    } else {
        varianceElement.className = 'fs-4 text-success';
        statusElement.innerHTML = '<i class="fas fa-check text-success"></i> Perfect';
    }
}

// Handle day close form submission
document.getElementById('closeDayForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const formData = new FormData(this);
    const cashCounted = parseFloat(document.getElementById('total-cash-counted').textContent.replace('$', ''));
    const expectedCash = {{ today_summary.cash_sales }};
    const variance = cashCounted - expectedCash;

    // Add cash count data
    const cashBreakdown = {};
    document.querySelectorAll('.denomination-input').forEach(input => {
        const denomination = input.dataset.value;
        const count = parseInt(input.value) || 0;
        if (count > 0) {
            cashBreakdown[denomination] = count;
        }
    });

    const data = {
        notes: formData.get('notes'),
        cash_counted: cashCounted,
        cash_variance: variance,
        cash_breakdown: cashBreakdown,
        supervisor_username: formData.get('supervisor_username'),
        supervisor_password: formData.get('supervisor_password')
    };

    // Show confirmation
    if (!confirm(`Are you sure you want to close the day?\n\nTotal Sales: ${{ today_summary.total_sales|floatformat:2 }}\nCash Variance: $${Math.abs(variance).toFixed(2)} ${variance >= 0 ? '(Over)' : '(Short)'}\n\nThis action cannot be undone.`)) {
        return;
    }

    try {
        const button = document.getElementById('closeDayBtn');
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Closing Day...';

        const response = await fetch('{% url "pharmacy:api_close_day" %}', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            alert('Day closed successfully!\n\nReport ID: ' + result.report_id);

            // Ask if user wants to view/print the report
            if (confirm('Do you want to view the end-of-day report?')) {
                window.open(`/pharmacy/pos/day-close-report/${result.report_id}/`, '_blank');
            }

            // Redirect to PoS dashboard
            window.location.href = '{% url "pharmacy:pos_dashboard" %}';
        } else {
            alert('Error closing day: ' + result.error);
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-lock"></i> Close Day & Generate Report';
        }
    } catch (error) {
        console.error('Close day error:', error);
        alert('An error occurred while closing the day');
        const button = document.getElementById('closeDayBtn');
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-lock"></i> Close Day & Generate Report';
    }
});
