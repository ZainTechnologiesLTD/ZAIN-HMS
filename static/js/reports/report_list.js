function deleteReport(reportId) {
    const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
    const form = document.getElementById('deleteForm');
    form.action = `/reports/${reportId}/delete/`;
    modal.show();
}

// Auto-refresh for processing reports
setInterval(function() {
    const processingCards = document.querySelectorAll('.badge.bg-warning');
    if (processingCards.length > 0) {
        location.reload();
    }
}, 30000); // Refresh every 30 seconds
