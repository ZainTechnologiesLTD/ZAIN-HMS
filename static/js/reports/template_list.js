let templateToDelete = null;

function deleteTemplate(templateId) {
    templateToDelete = templateId;
    const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
    modal.show();
}

function confirmDelete() {
    if (templateToDelete) {
        // In a real implementation, this would make an AJAX call to delete the template
        fetch(`/reports/templates/${templateToDelete}/delete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': '{{ csrf_token }}',
                'Content-Type': 'application/json',
            }
        }).then(response => {
            if (response.ok) {
                location.reload();
            }
        }).catch(error => {
            console.error('Error:', error);
        });
    }
}

function createSuggestedTemplate(templateType) {
    let templateData = {};

    switch(templateType) {
        case 'patient-summary':
            templateData = {
                name: 'Patient Summary Report',
                report_type: 'PATIENT',
                description: 'Comprehensive overview of patient demographics and statistics',
                columns: JSON.stringify([
                    'patient_id', 'full_name', 'age', 'gender',
                    'blood_group', 'phone', 'registration_date'
                ]),
                default_filters: JSON.stringify({
                    'status': 'active'
                })
            };
            break;

        case 'daily-appointments':
            templateData = {
                name: 'Daily Appointments Report',
                report_type: 'APPOINTMENT',
                description: 'Today\'s appointment schedule and status',
                columns: JSON.stringify([
                    'appointment_id', 'patient_name', 'doctor_name',
                    'appointment_time', 'status', 'type'
                ]),
                default_filters: JSON.stringify({
                    'appointment_date': 'today'
                })
            };
            break;

        case 'financial-overview':
            templateData = {
                name: 'Financial Overview Report',
                report_type: 'FINANCIAL',
                description: 'Revenue, billing, and financial performance summary',
                columns: JSON.stringify([
                    'date', 'total_revenue', 'total_bills',
                    'paid_amount', 'pending_amount', 'collection_rate'
                ]),
                default_filters: JSON.stringify({
                    'period': 'month'
                })
            };
            break;

        case 'emergency-cases':
            templateData = {
                name: 'Emergency Cases Report',
                report_type: 'EMERGENCY',
                description: 'Emergency department cases and response times',
                columns: JSON.stringify([
                    'case_id', 'patient_name', 'admission_time',
                    'severity_level', 'status', 'discharge_time'
                ]),
                default_filters: JSON.stringify({
                    'status': 'all'
                })
            };
            break;
    }

    // Redirect to template creation form with pre-filled data
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '{% url "reports:template_create" %}';

    // Add CSRF token
    const csrfToken = document.createElement('input');
    csrfToken.type = 'hidden';
    csrfToken.name = 'csrfmiddlewaretoken';
    csrfToken.value = '{{ csrf_token }}';
    form.appendChild(csrfToken);

    // Add template data
    for (const [key, value] of Object.entries(templateData)) {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = key;
        input.value = value;
        form.appendChild(input);
    }

    document.body.appendChild(form);
    form.submit();
}

// Add click handlers for template cards
document.querySelectorAll('.template-card').forEach(card => {
    card.addEventListener('click', function(e) {
        // Don't trigger if clicking on action buttons
        if (!e.target.closest('.template-actions')) {
            const useLink = this.querySelector('a[href*="use_template"]');
            if (useLink) {
                window.location.href = useLink.href;
            }
        }
    });
});
