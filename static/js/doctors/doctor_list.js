// Select All functionality
document.addEventListener('DOMContentLoaded', function() {
    const selectAllCheckbox = document.getElementById('selectAll');
    const doctorCheckboxes = document.querySelectorAll('.doctor-checkbox');
    const bulkActionsBar = document.getElementById('bulkActionsBar');
    const selectedCountSpan = document.getElementById('selectedCount');

    // Select All checkbox handler
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            doctorCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateBulkActionsVisibility();
        });
    }

    // Individual checkbox handlers
    doctorCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            // Update "Select All" checkbox state
            const checkedBoxes = document.querySelectorAll('.doctor-checkbox:checked');
            selectAllCheckbox.checked = checkedBoxes.length === doctorCheckboxes.length;
            selectAllCheckbox.indeterminate = checkedBoxes.length > 0 && checkedBoxes.length < doctorCheckboxes.length;

            updateBulkActionsVisibility();
        });
    });

    function updateBulkActionsVisibility() {
        const checkedBoxes = document.querySelectorAll('.doctor-checkbox:checked');
        if (checkedBoxes.length > 0) {
            bulkActionsBar.classList.remove('d-none');
            selectedCountSpan.textContent = checkedBoxes.length;
        } else {
            bulkActionsBar.classList.add('d-none');
        }
    }
});

// Bulk actions functions
function getSelectedDoctorIds() {
    const checkedBoxes = document.querySelectorAll('.doctor-checkbox:checked');
    return Array.from(checkedBoxes).map(cb => cb.value);
}

function bulkActivate() {
    const selectedIds = getSelectedDoctorIds();
    if (selectedIds.length === 0) {
        alert('Please select at least one doctor.');
        return;
    }

    if (confirm(`Are you sure you want to activate ${selectedIds.length} doctor(s)?`)) {
        submitBulkAction('activate', selectedIds);
    }
}

function bulkDeactivate() {
    const selectedIds = getSelectedDoctorIds();
    if (selectedIds.length === 0) {
        alert('Please select at least one doctor.');
        return;
    }

    if (confirm(`Are you sure you want to deactivate ${selectedIds.length} doctor(s)?`)) {
        submitBulkAction('deactivate', selectedIds);
    }
}

function bulkDelete() {
    const selectedIds = getSelectedDoctorIds();
    if (selectedIds.length === 0) {
        alert('Please select at least one doctor.');
        return;
    }

    if (confirm(`Are you sure you want to delete ${selectedIds.length} doctor(s)? This action cannot be undone.`)) {
        submitBulkAction('delete', selectedIds);
    }
}

function submitBulkAction(action, selectedIds) {
    // Create a form to submit the bulk action
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '{% url "doctors:doctor_bulk_action" %}';

    // Add CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const csrfField = document.createElement('input');
    csrfField.type = 'hidden';
    csrfField.name = 'csrfmiddlewaretoken';
    csrfField.value = csrfToken;
    form.appendChild(csrfField);

    // Add action
    const actionField = document.createElement('input');
    actionField.type = 'hidden';
    actionField.name = 'action';
    actionField.value = action;
    form.appendChild(actionField);

    // Add selected IDs
    selectedIds.forEach(id => {
        const idField = document.createElement('input');
        idField.type = 'hidden';
        idField.name = 'selected_doctors';
        idField.value = id;
        form.appendChild(idField);
    });

    // Submit the form
    document.body.appendChild(form);
    form.submit();
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        // Show success message
        const toast = document.createElement('div');
        toast.className = 'toast show position-fixed top-0 end-0 m-3';
        toast.style.zIndex = '9999';
        toast.innerHTML = `
            <div class="toast-body bg-success text-white rounded">
                <i class="fas fa-check-circle me-2"></i>ID copied to clipboard: ${text}
            </div>
        `;
        document.body.appendChild(toast);
        setTimeout(() => {
            toast.remove();
        }, 2000);
    }).catch(function(err) {
        console.error('Could not copy text: ', err);
    });
}

// Auto-hide alerts
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert:not(#bulkActionsBar)');
        alerts.forEach(function(alert) {
            if (alert.classList.contains('alert-dismissible')) {
                var closeBtn = alert.querySelector('.btn-close');
                if (closeBtn) {
                    closeBtn.click();
                }
            }
        });
    }, 5000);
});
