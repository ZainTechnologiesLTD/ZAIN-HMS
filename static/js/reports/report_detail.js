function deleteReport(reportId) {
    const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
    modal.show();
}

function duplicateReport() {
    // Redirect to generate report with pre-filled data
    const url = new URL('{% url "reports:generate_report" %}', window.location.origin);
    url.searchParams.set('duplicate', '{{ report.pk }}');
    window.location.href = url;
}

function shareReport() {
    if (navigator.share) {
        navigator.share({
            title: '{{ report.name }}',
            text: 'Hospital Report: {{ report.name }}',
            url: window.location.href
        });
    } else {
        // Fallback: copy to clipboard
        navigator.clipboard.writeText(window.location.href).then(() => {
            alert('Report link copied to clipboard!');
        });
    }
}

function retryReport() {
    if (confirm('Are you sure you want to retry generating this report?')) {
        // In a real implementation, this would trigger a retry
        fetch(`{% url 'reports:generate_report' %}`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': '{{ csrf_token }}',
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                'retry': '{{ report.pk }}',
                'name': '{{ report.name }}',
                'report_type': '{{ report.report_type }}',
                'format': '{{ report.format }}'
            })
        }).then(() => {
            location.reload();
        });
    }
}

// Auto-refresh for processing reports
{% if report.status == 'PROCESSING' or report.status == 'PENDING' %}
setInterval(function() {
    location.reload();
}, 10000); // Refresh every 10 seconds
{% endif %}
