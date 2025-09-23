// Date range helpers
function setDateRange(period) {
    const today = new Date();
    const dateFromInput = document.getElementById('{{ form.date_from.id_for_label }}');
    const dateToInput = document.getElementById('{{ form.date_to.id_for_label }}');

    let fromDate, toDate;

    switch(period) {
        case 'today':
            fromDate = toDate = today;
            break;
        case 'week':
            fromDate = new Date(today.getFullYear(), today.getMonth(), today.getDate() - today.getDay());
            toDate = today;
            break;
        case 'month':
            fromDate = new Date(today.getFullYear(), today.getMonth(), 1);
            toDate = today;
            break;
        case 'quarter':
            const quarter = Math.floor(today.getMonth() / 3);
            fromDate = new Date(today.getFullYear(), quarter * 3, 1);
            toDate = today;
            break;
    }

    dateFromInput.value = fromDate.toISOString().split('T')[0];
    dateToInput.value = toDate.toISOString().split('T')[0];

    updatePreview();
}

// Template helpers
function useTemplate(templateType) {
    const nameInput = document.getElementById('{{ form.name.id_for_label }}');
    const typeSelect = document.getElementById('{{ form.report_type.id_for_label }}');
    const formatSelect = document.getElementById('{{ form.format.id_for_label }}');

    switch(templateType) {
        case 'patient-summary':
            nameInput.value = 'Patient Summary Report - ' + new Date().toLocaleDateString();
            typeSelect.value = 'PATIENT';
            formatSelect.value = 'PDF';
            setDateRange('month');
            break;
        case 'appointment-daily':
            nameInput.value = 'Daily Appointments - ' + new Date().toLocaleDateString();
            typeSelect.value = 'APPOINTMENT';
            formatSelect.value = 'EXCEL';
            setDateRange('today');
            break;
        case 'financial-monthly':
            nameInput.value = 'Monthly Financial Report - ' + new Date().toLocaleDateString();
            typeSelect.value = 'FINANCIAL';
            formatSelect.value = 'PDF';
            setDateRange('month');
            break;
        case 'billing-pending':
            nameInput.value = 'Pending Bills Report - ' + new Date().toLocaleDateString();
            typeSelect.value = 'BILLING';
            formatSelect.value = 'EXCEL';
            break;
    }

    updatePreview();
}

// Preview updater
function updatePreview() {
    const type = document.getElementById('{{ form.report_type.id_for_label }}').value;
    const format = document.getElementById('{{ form.format.id_for_label }}').value;
    const dateFrom = document.getElementById('{{ form.date_from.id_for_label }}').value;
    const dateTo = document.getElementById('{{ form.date_to.id_for_label }}').value;

    if (type || format || dateFrom || dateTo) {
        document.getElementById('preview-details').style.display = 'block';
        document.getElementById('preview-type').textContent = type || '-';
        document.getElementById('preview-format').textContent = format || '-';

        let dateRange = '-';
        if (dateFrom && dateTo) {
            dateRange = `${dateFrom} to ${dateTo}`;
        } else if (dateFrom) {
            dateRange = `From ${dateFrom}`;
        } else if (dateTo) {
            dateRange = `Until ${dateTo}`;
        }
        document.getElementById('preview-dates').textContent = dateRange;

        // Simulate record estimation
        if (type) {
            const estimates = {
                'PATIENT': '150-300',
                'APPOINTMENT': '50-200',
                'BILLING': '100-500',
                'FINANCIAL': '20-100'
            };
            document.getElementById('preview-records').textContent = estimates[type] || '10-100';
        }
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    // Update preview on form changes
    document.querySelectorAll('select, input[type="date"]').forEach(element => {
        element.addEventListener('change', updatePreview);
    });

    // Form validation
    (function() {
        'use strict';
        window.addEventListener('load', function() {
            var forms = document.getElementsByClassName('needs-validation');
            var validation = Array.prototype.filter.call(forms, function(form) {
                form.addEventListener('submit', function(event) {
                    if (form.checkValidity() === false) {
                        event.preventDefault();
                        event.stopPropagation();
                    }
                    form.classList.add('was-validated');
                }, false);
            });
        }, false);
    })();
});
