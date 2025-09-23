// CSRF token
const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '{{ csrf_token }}';
let currentRefundTransactionId = null;

function processRefund(transactionId) {
    currentRefundTransactionId = transactionId;
    const modal = new bootstrap.Modal(document.getElementById('refundModal'));
    modal.show();
}

document.getElementById('refundForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    if (!currentRefundTransactionId) return;

    const formData = new FormData(this);
    const data = {
        transaction_id: currentRefundTransactionId,
        refund_reason: formData.get('refund_reason'),
        notes: formData.get('notes')
    };

    try {
        const response = await fetch('{% url "pharmacy:api_process_refund" %}', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            alert('Refund processed successfully!');
            location.reload();
        } else {
            alert('Error processing refund: ' + result.error);
        }
    } catch (error) {
        console.error('Refund error:', error);
        alert('An error occurred while processing the refund');
    }
});

// Auto-submit form on preset filter clicks
document.addEventListener('click', function(e) {
    if (e.target.matches('a[href*="?preset="]')) {
        e.preventDefault();
        const url = new URL(e.target.href);
        const preset = url.searchParams.get('preset');

        // Clear existing form values
        const form = document.querySelector('form');
        form.querySelectorAll('input, select').forEach(input => {
            if (input.name !== 'preset') {
                input.value = '';
            }
        });

        // Set preset and submit
        const presetInput = document.createElement('input');
        presetInput.type = 'hidden';
        presetInput.name = 'preset';
        presetInput.value = preset;
        form.appendChild(presetInput);
        form.submit();
    }
});
