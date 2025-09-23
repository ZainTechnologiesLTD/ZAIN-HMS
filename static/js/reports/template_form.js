// Available fields for each report type
const availableFields = {
    'PATIENT': [
        'patient_id', 'full_name', 'age', 'gender', 'blood_group',
        'phone', 'email', 'address', 'registration_date', 'status'
    ],
    'APPOINTMENT': [
        'appointment_id', 'patient_name', 'doctor_name', 'department',
        'appointment_date', 'appointment_time', 'status', 'type', 'notes'
    ],
    'BILLING': [
        'bill_id', 'patient_name', 'amount', 'paid_amount', 'pending_amount',
        'bill_date', 'due_date', 'status', 'payment_method'
    ],
    'FINANCIAL': [
        'date', 'total_revenue', 'total_bills', 'paid_amount',
        'pending_amount', 'collection_rate', 'department_wise'
    ],
    'DOCTOR': [
        'doctor_id', 'full_name', 'specialization', 'department',
        'patients_count', 'appointments_count', 'revenue_generated'
    ],
    'EMERGENCY': [
        'case_id', 'patient_name', 'admission_time', 'discharge_time',
        'severity_level', 'status', 'attending_doctor', 'outcome'
    ]
};

let selectedColumns = [];
let selectedFilters = {};

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    // Load existing data if editing
    {% if form.instance.pk %}
    try {
        selectedColumns = {{ form.instance.columns|safe }};
        selectedFilters = {{ form.instance.default_filters|safe }};
        updateColumnBuilder();
        updateFilterBuilder();
    } catch (e) {
        console.error('Error loading existing data:', e);
    }
    {% endif %}

    // Update preview when report type changes
    document.getElementById('{{ form.report_type.id_for_label }}').addEventListener('change', function() {
        updateAvailableFields();
        updatePreview();
    });

    // Update preview when form changes
    document.querySelectorAll('input, textarea, select').forEach(element => {
        element.addEventListener('input', updatePreview);
        element.addEventListener('change', updatePreview);
    });

    // Initial setup
    updateAvailableFields();
    updatePreview();
});

function updateAvailableFields() {
    const reportType = document.getElementById('{{ form.report_type.id_for_label }}').value;
    const fieldsContainer = document.getElementById('available-fields');
    const referenceContainer = document.getElementById('field-reference');

    if (reportType && availableFields[reportType]) {
        // Update available fields
        fieldsContainer.innerHTML = '';
        availableFields[reportType].forEach(field => {
            const badge = document.createElement('span');
            badge.className = 'badge bg-light text-dark border';
            badge.textContent = field;
            badge.style.cursor = 'pointer';
            badge.onclick = () => addColumnFromField(field);
            fieldsContainer.appendChild(badge);
        });

        // Update field reference
        referenceContainer.innerHTML = availableFields[reportType].map(field =>
            `<span class="badge bg-outline-primary me-1 mb-1">${field}</span>`
        ).join('');
    } else {
        fieldsContainer.innerHTML = '<span class="text-muted">Select report type first</span>';
        referenceContainer.innerHTML = '<p class="text-muted small">Select a report type to see available fields</p>';
    }
}

function addColumnFromField(field) {
    if (!selectedColumns.includes(field)) {
        selectedColumns.push(field);
        updateColumnBuilder();
        updateColumnsJSON();
    }
}

function addColumn() {
    const columnName = prompt('Enter column name:');
    if (columnName && !selectedColumns.includes(columnName)) {
        selectedColumns.push(columnName);
        updateColumnBuilder();
        updateColumnsJSON();
    }
}

function removeColumn(index) {
    selectedColumns.splice(index, 1);
    updateColumnBuilder();
    updateColumnsJSON();
}

function updateColumnBuilder() {
    const columnList = document.getElementById('column-list');
    columnList.innerHTML = '';

    selectedColumns.forEach((column, index) => {
        const columnItem = document.createElement('div');
        columnItem.className = 'column-item';
        columnItem.innerHTML = `
            <span class="drag-handle">
                <i class="fas fa-grip-vertical"></i>
            </span>
            <span class="flex-grow-1">${column}</span>
            <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeColumn(${index})">
                <i class="fas fa-times"></i>
            </button>
        `;
        columnList.appendChild(columnItem);
    });
}

function updateColumnsJSON() {
    document.getElementById('{{ form.columns.id_for_label }}').value = JSON.stringify(selectedColumns);
    updatePreview();
}

function addFilter() {
    const filterKey = prompt('Enter filter key:');
    const filterValue = prompt('Enter filter value:');

    if (filterKey && filterValue) {
        selectedFilters[filterKey] = filterValue;
        updateFilterBuilder();
        updateFiltersJSON();
    }
}

function removeFilter(key) {
    delete selectedFilters[key];
    updateFilterBuilder();
    updateFiltersJSON();
}

function updateFilterBuilder() {
    const filterList = document.getElementById('filter-list');
    filterList.innerHTML = '';

    Object.entries(selectedFilters).forEach(([key, value]) => {
        const filterItem = document.createElement('div');
        filterItem.className = 'column-item';
        filterItem.innerHTML = `
            <span class="flex-grow-1">
                <strong>${key}:</strong> ${value}
            </span>
            <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeFilter('${key}')">
                <i class="fas fa-times"></i>
            </button>
        `;
        filterList.appendChild(filterItem);
    });
}

function updateFiltersJSON() {
    document.getElementById('{{ form.default_filters.id_for_label }}').value = JSON.stringify(selectedFilters);
    updatePreview();
}

function updatePreview() {
    const name = document.getElementById('{{ form.name.id_for_label }}').value;
    const reportType = document.getElementById('{{ form.report_type.id_for_label }}').value;
    const description = document.getElementById('{{ form.description.id_for_label }}').value;

    const preview = document.getElementById('template-preview');

    if (name || reportType || description) {
        preview.innerHTML = `
            <div>
                <h6>${name || 'Untitled Template'}</h6>
                <p class="text-muted small">${description || 'No description'}</p>

                <div class="mb-3">
                    <strong>Type:</strong> ${reportType || 'Not selected'}
                </div>

                <div class="mb-3">
                    <strong>Columns (${selectedColumns.length}):</strong><br>
                    ${selectedColumns.length > 0 ?
                        selectedColumns.map(col => `<span class="badge bg-primary me-1">${col}</span>`).join('') :
                        '<span class="text-muted">No columns selected</span>'
                    }
                </div>

                <div>
                    <strong>Filters (${Object.keys(selectedFilters).length}):</strong><br>
                    ${Object.keys(selectedFilters).length > 0 ?
                        Object.entries(selectedFilters).map(([k, v]) => `<span class="badge bg-secondary me-1">${k}=${v}</span>`).join('') :
                        '<span class="text-muted">No default filters</span>'
                    }
                </div>
            </div>
        `;
    }
}

function testTemplate() {
    {% if form.instance.pk %}
    // For existing templates, use the template directly
    window.location.href = "{% url 'reports:use_template' form.instance.pk %}";
    {% else %}
    // For new templates, save first then redirect
    const form = document.querySelector('form');
    const formData = new FormData(form);

    fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    }).then(response => {
        if (response.ok) {
            return response.json();
        }
        throw new Error('Failed to save template');
    }).then(data => {
        if (data.redirect_url) {
            window.location.href = data.redirect_url;
        } else {
            window.location.href = "{% url 'reports:template_list' %}";
        }
    }).catch(error => {
        alert('Please save the template first before testing.');
    });
    {% endif %}
}

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

// CSRF Cookie helper function
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
