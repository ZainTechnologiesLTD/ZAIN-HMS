// Real-time updates
function refreshData() {
    location.reload();
}

// Auto-refresh every 30 seconds
setInterval(refreshData, 30000);

function newEmergencyCase() {
    window.location.href = '{% url "emergency:case_create" %}';
}

function startTreatment(caseId) {
    if (confirm('Start treatment for this patient?')) {
        fetch(`/emergency/cases/${caseId}/start-treatment/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': '{{ csrf_token }}',
                'Content-Type': 'application/json',
            }
        }).then(response => {
            if (response.ok) {
                location.reload();
            }
        });
    }
}

function updateVitals(caseId) {
    fetch(`/emergency/cases/${caseId}/vitals-form/`)
    .then(response => response.text())
    .then(html => {
        document.querySelector('#emergencyModal .modal-content').innerHTML = html;
        new bootstrap.Modal(document.getElementById('emergencyModal')).show();
    });
}

function emergencyAlert(caseId) {
    if (confirm('Send emergency alert for this critical case?')) {
        fetch(`/emergency/cases/${caseId}/alert/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': '{{ csrf_token }}',
                'Content-Type': 'application/json',
            }
        }).then(response => {
            if (response.ok) {
                alert('Emergency alert sent to all available staff!');
            }
        });
    }
}

// Update last updated time
setInterval(function() {
    document.getElementById('lastUpdate').textContent = 'Updated just now';
}, 1000);
