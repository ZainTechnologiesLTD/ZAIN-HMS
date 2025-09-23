function recordPayment() {
    const modal = new bootstrap.Modal(document.getElementById('paymentModal'));
    modal.show();
}

function emailBill() {
    if (confirm('Send bill to patient email?')) {
        fetch(`{% url 'billing:email_bill' bill.pk %}`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': '{{ csrf_token }}',
                'Content-Type': 'application/json',
            }
        }).then(response => {
            if (response.ok) {
                alert('Bill sent successfully!');
            } else {
                alert('Failed to send bill. Please try again.');
            }
        });
    }
}

function duplicateBill() {
    if (confirm('Create a copy of this bill?')) {
        window.location.href = `{% url 'billing:bill_duplicate' bill.pk %}`;
    }
}
