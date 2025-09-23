function recordPayment(billId) {
    document.getElementById('paymentBillId').value = billId;
    const modal = new bootstrap.Modal(document.getElementById('paymentModal'));
    modal.show();
}

// Auto-refresh for real-time updates
setInterval(function() {
    // Check if there are any pending bills and refresh if needed
    const pendingBadges = document.querySelectorAll('.badge.bg-warning');
    if (pendingBadges.length > 0) {
        // Optional: Add subtle refresh indicator
    }
}, 30000); // Every 30 seconds
