let currentRecommendationId = null;

// Acknowledge alert
function acknowledgeAlert(alertId) {
    if (confirm('Acknowledge this alert?')) {
        fetch(`/emr/alerts/${alertId}/action/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: 'action=acknowledge'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Alert acknowledged successfully', 'success');
                location.reload();
            } else {
                showToast(data.error || 'Failed to acknowledge alert', 'error');
            }
        })
        .catch(error => {
            console.error('Error acknowledging alert:', error);
            showToast('Error acknowledging alert', 'error');
        });
    }
}

// View recommendation details
function viewRecommendationDetails(recommendationId) {
    currentRecommendationId = recommendationId;

    fetch(`/emr/api/recommendation/${recommendationId}/`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('recommendationDetailsContent').innerHTML = `
                <h6>${data.recommendation_type}</h6>
                <div class="alert alert-info">
                    <strong>Recommendation:</strong><br>
                    ${data.recommendation_text}
                </div>
                <p><strong>Confidence Score:</strong> ${data.confidence_score}%</p>
                <p><strong>Supporting Evidence:</strong></p>
                <ul>
                    ${data.supporting_evidence.map(evidence => `<li>${evidence}</li>`).join('')}
                </ul>
                <p><strong>Expected Outcome:</strong> ${data.expected_outcome || 'Improved patient care'}</p>
            `;

            new bootstrap.Modal(document.getElementById('recommendationDetailsModal')).show();
        })
        .catch(error => {
            console.error('Error fetching recommendation details:', error);
            showToast('Error loading recommendation details', 'error');
        });
}

// Implement recommendation
document.getElementById('implementRecommendationBtn').addEventListener('click', function() {
    if (currentRecommendationId && confirm('Implement this AI recommendation?')) {
        fetch('/emr/clinical-decisions/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: `recommendation_id=${currentRecommendationId}&action=implement`
        })
        .then(response => {
            if (response.ok) {
                showToast('Recommendation implemented successfully', 'success');
                bootstrap.Modal.getInstance(document.getElementById('recommendationDetailsModal')).hide();
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
});

// Quick action functions
function generateTreatmentPlan() {
    window.location.href = `/emr/ai/treatment-plan/?patient_id={{ patient.id }}`;
}

function checkMedicationInteractions() {
    window.location.href = `/emr/ai/drug-interactions/?patient_id={{ patient.id }}`;
}

function scheduleFollowUp() {
    window.location.href = `/appointments/schedule/?patient_id={{ patient.id }}`;
}

function exportAnalysis() {
    // Generate PDF export of the analysis
    fetch(`/emr/ai/patient-analysis/{{ patient.id }}/export/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.blob())
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `ai_analysis_{{ patient.get_full_name|slugify }}_{{ "now"|date:"Y-m-d" }}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    })
    .catch(error => {
        console.error('Error exporting analysis:', error);
        showToast('Error exporting analysis', 'error');
    });
}

// Utility functions
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
    const toast = document.createElement('div');
    toast.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 5000);
}

// Initialize confidence bars animation
document.addEventListener('DOMContentLoaded', function() {
    const confidenceBars = document.querySelectorAll('.confidence-fill');
    confidenceBars.forEach(bar => {
        const width = bar.style.width;
        bar.style.width = '0%';
        setTimeout(() => {
            bar.style.width = width;
        }, 500);
    });
});
