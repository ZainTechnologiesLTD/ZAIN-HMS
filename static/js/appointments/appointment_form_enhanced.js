// Enhanced Appointment Form JavaScript
document.addEventListener('DOMContentLoaded', function() {
    console.log('Enhanced appointment form JS loaded');

    // Auto-save functionality for draft appointments
    let autoSaveTimeout;
    const form = document.getElementById('appointmentForm');

    if (form) {
        // Auto-save on form changes
        form.addEventListener('input', function() {
            clearTimeout(autoSaveTimeout);
            autoSaveTimeout = setTimeout(autoSaveDraft, 3000);
        });

        // Prevent accidental navigation
        window.addEventListener('beforeunload', function(e) {
            if (hasUnsavedChanges()) {
                e.preventDefault();
                e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
            }
        });
    }

    // Patient search enhancement
    const searchInputs = document.querySelectorAll('#search_name, #search_phone');
    searchInputs.forEach(input => {
        input.addEventListener('input', debounce(searchPatients, 300));
    });

    // Doctor selection enhancement
    const doctorSelect = document.getElementById('id_doctor');
    if (doctorSelect) {
        doctorSelect.addEventListener('change', updateDoctorSchedule);
    }

    // Date/time validation
    const dateInput = document.getElementById('id_appointment_date');
    const timeInput = document.getElementById('id_appointment_time');

    if (dateInput && timeInput) {
        dateInput.addEventListener('change', validateAppointmentDateTime);
        timeInput.addEventListener('change', validateAppointmentDateTime);
    }

    // Priority level visual feedback
    const prioritySelect = document.getElementById('id_priority');
    if (prioritySelect) {
        prioritySelect.addEventListener('change', updatePriorityStyling);
    }

    // Form validation enhancement
    if (form) {
        form.addEventListener('submit', function(e) {
            if (!validateForm()) {
                e.preventDefault();
                return false;
            }
            showLoadingState();
        });
    }

    // Initialize tooltips
    initializeTooltips();

    // Initialize form state
    updateFormState();
});

function autoSaveDraft() {
    // Implement auto-save functionality
    console.log('Auto-saving draft...');
    // This would typically send a request to save the form data as a draft
}

function hasUnsavedChanges() {
    // Check if form has unsaved changes
    const form = document.getElementById('appointmentForm');
    if (!form) return false;

    // Simple check - in a real implementation, you'd compare with original values
    return form.querySelectorAll('input:not([type="hidden"]), select, textarea').some(el => el.value !== el.defaultValue);
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function searchPatients() {
    const name = document.getElementById('search_name').value;
    const phone = document.getElementById('search_phone').value;

    if (name.length < 2 && phone.length < 2) return;

    // Trigger HTMX request or AJAX call
    const searchContainer = document.getElementById('patient-search-results');
    if (searchContainer) {
        // This would be handled by HTMX attributes in the template
        console.log('Searching patients:', { name, phone });
    }
}

function updateDoctorSchedule() {
    const doctorId = document.getElementById('id_doctor').value;
    if (!doctorId) return;

    // Update available time slots based on doctor selection
    console.log('Updating schedule for doctor:', doctorId);
    // This would typically fetch doctor's available slots
}

function validateAppointmentDateTime() {
    const dateInput = document.getElementById('id_appointment_date');
    const timeInput = document.getElementById('id_appointment_time');

    if (!dateInput || !timeInput) return;

    const selectedDate = new Date(dateInput.value);
    const now = new Date();

    // Check if date is in the past
    if (selectedDate < now.setHours(0,0,0,0)) {
        showError('Cannot schedule appointments in the past');
        return false;
    }

    // Additional validation logic here
    return true;
}

function updatePriorityStyling() {
    const prioritySelect = document.getElementById('id_priority');
    if (!prioritySelect) return;

    const priority = prioritySelect.value;
    const formCard = document.querySelector('.card');

    // Remove existing priority classes
    formCard.classList.remove('border-warning', 'border-danger', 'border-info');

    // Add appropriate styling based on priority
    switch(priority) {
        case 'HIGH':
            formCard.classList.add('border-danger');
            break;
        case 'MEDIUM':
            formCard.classList.add('border-warning');
            break;
        case 'LOW':
            formCard.classList.add('border-info');
            break;
    }
}

function validateForm() {
    let isValid = true;
    const errors = [];

    // Required field validation
    const requiredFields = ['id_patient', 'id_doctor', 'id_appointment_date', 'id_appointment_time'];
    requiredFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field && !field.value.trim()) {
            errors.push(`${field.name} is required`);
            field.classList.add('is-invalid');
            isValid = false;
        } else if (field) {
            field.classList.remove('is-invalid');
        }
    });

    // Date/time validation
    if (!validateAppointmentDateTime()) {
        isValid = false;
    }

    // Show errors if any
    if (errors.length > 0) {
        showErrors(errors);
    }

    return isValid;
}

function showError(message) {
    // Use SweetAlert2 if available, otherwise use alert
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            icon: 'error',
            title: 'Validation Error',
            text: message
        });
    } else {
        alert(message);
    }
}

function showErrors(errors) {
    const errorHtml = errors.map(error => `<li>${error}</li>`).join('');
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            icon: 'error',
            title: 'Please fix the following errors:',
            html: `<ul class="text-start">${errorHtml}</ul>`
        });
    } else {
        alert('Please fix the following errors:\n' + errors.join('\n'));
    }
}

function showLoadingState() {
    const submitBtn = document.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saving...';
    }
}

function initializeTooltips() {
    // Initialize Bootstrap tooltips if available
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

function updateFormState() {
    // Update form elements based on current state
    updatePriorityStyling();

    // Set default date to today if not set
    const dateInput = document.getElementById('id_appointment_date');
    if (dateInput && !dateInput.value) {
        const today = new Date().toISOString().split('T')[0];
        dateInput.value = today;
    }
}

// Utility functions for enhanced UX
function showSuccess(message) {
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            icon: 'success',
            title: 'Success',
            text: message,
            timer: 3000,
            showConfirmButton: false
        });
    }
}

function confirmAction(message, callback) {
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            title: 'Are you sure?',
            text: message,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#3085d6',
            cancelButtonColor: '#d33',
            confirmButtonText: 'Yes, proceed'
        }).then((result) => {
            if (result.isConfirmed) {
                callback();
            }
        });
    } else {
        if (confirm(message)) {
            callback();
        }
    }
}
