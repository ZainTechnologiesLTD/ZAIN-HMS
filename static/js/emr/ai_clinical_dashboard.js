// Global variables
let currentAlertId = null;
let currentRecommendationId = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    initializeAIPerformanceChart();
    setupRealTimeUpdates();
});

// Initialize AI Performance Chart
function initializeAIPerformanceChart() {
    const ctx = document.getElementById('aiPerformanceChart').getContext('2d');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Diagnostic Accuracy',
                data: [87, 89, 91, 85, 88, 92, 87],
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                tension: 0.4,
                fill: true
            }, {
                label: 'Alert Precision',
                data: [89, 91, 88, 93, 90, 89, 92],
                borderColor: '#764ba2',
                backgroundColor: 'rgba(118, 75, 162, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'AI System Performance (Last 7 Days)'
                }
            }
        }
    });
}

// Alert Management Functions
function viewAlert(alertId) {
    currentAlertId = alertId;

    // Fetch alert details
    fetch(`/emr/api/alert/${alertId}/`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('alertDetails').innerHTML = `
                <h6>${data.title}</h6>
                <p><strong>Patient:</strong> ${data.patient_name}</p>
                <p><strong>Severity:</strong> <span class="badge bg-${data.severity.toLowerCase()}">${data.severity}</span></p>
                <p><strong>Description:</strong> ${data.description}</p>
                <p><strong>Created:</strong> ${data.created_at}</p>
            `;

            new bootstrap.Modal(document.getElementById('alertActionModal')).show();
        })
        .catch(error => {
            console.error('Error fetching alert details:', error);
            showToast('Error loading alert details', 'error');
        });
}

function acknowledgeAlert(alertId) {
    if (confirm('Acknowledge this alert?')) {
        processAlertAction('acknowledge', alertId);
    }
}

function processAlertAction(action, alertId = null) {
    const id = alertId || currentAlertId;
    const notes = document.getElementById('alertNotes')?.value || '';

    fetch(`/emr/alerts/${id}/action/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: `action=${action}&notes=${encodeURIComponent(notes)}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(`Alert ${action}d successfully`, 'success');
            location.reload(); // Refresh to update UI
        } else {
            showToast(data.error || 'Action failed', 'error');
        }
    })
    .catch(error => {
        console.error('Error processing alert action:', error);
        showToast('Error processing action', 'error');
    });

    // Close modal if open
    const modal = bootstrap.Modal.getInstance(document.getElementById('alertActionModal'));
    if (modal) modal.hide();
}

// Recommendation Management Functions
function viewRecommendation(recommendationId) {
    currentRecommendationId = recommendationId;

    // Fetch recommendation details
    fetch(`/emr/api/recommendation/${recommendationId}/`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('recommendationDetails').innerHTML = `
                <h6>${data.recommendation_type}</h6>
                <p><strong>Patient:</strong> ${data.patient_name}</p>
                <p><strong>Confidence:</strong> ${data.confidence_score}%</p>
                <div class="alert alert-info">
                    <strong>Recommendation:</strong><br>
                    ${data.recommendation_text}
                </div>
                <p><strong>Supporting Evidence:</strong></p>
                <ul>
                    ${data.supporting_evidence.map(evidence => `<li>${evidence}</li>`).join('')}
                </ul>
            `;

            new bootstrap.Modal(document.getElementById('recommendationModal')).show();
        })
        .catch(error => {
            console.error('Error fetching recommendation details:', error);
            showToast('Error loading recommendation details', 'error');
        });
}

function implementRecommendation(recommendationId) {
    if (confirm('Implement this AI recommendation?')) {
        fetch(`/emr/clinical-decisions/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: `recommendation_id=${recommendationId}&action=implement`
        })
        .then(response => {
            if (response.ok) {
                showToast('Recommendation implemented successfully', 'success');
                location.reload();
            } else {
                showToast('Failed to implement recommendation', 'error');
            }
        })
        .catch(error => {
            console.error('Error implementing recommendation:', error);
            showToast('Error implementing recommendation', 'error');
        });
    }
}

function implementRecommendationFromModal() {
    implementRecommendation(currentRecommendationId);

    const modal = bootstrap.Modal.getInstance(document.getElementById('recommendationModal'));
    if (modal) modal.hide();
}

// Patient Analysis Functions
function viewPatientAnalysis(patientId) {
    window.location.href = `/emr/ai/patient-analysis/${patientId}/`;
}

function viewPatientRecord(patientId) {
    window.location.href = `/patients/${patientId}/`;
}

// Quick Action Functions
function runVitalSignsAnalysis() {
    window.location.href = '/emr/ai/vital-signs-analysis/';
}

function checkDrugInteractions() {
    window.location.href = '/emr/ai/drug-interactions/';
}

function analyzeLabResults() {
    window.location.href = '/emr/ai/lab-analysis/';
}

function generateTreatmentPlan() {
    window.location.href = '/emr/ai/treatment-plan/';
}

// Real-time Updates
function setupRealTimeUpdates() {
    // Refresh dashboard data every 30 seconds
    setInterval(function() {
        fetch(window.location.href, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.text())
        .then(html => {
            // Update specific sections without full page reload
            // This would require more sophisticated partial update logic
        })
        .catch(error => {
            console.error('Error updating dashboard:', error);
        });
    }, 30000);
}

// Utility Functions
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function showToast(message, type = 'info') {
    // Create toast notification
    const toast = document.createElement('div');
    toast.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(toast);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 5000);
}
