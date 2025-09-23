/**
 * Modern Patient List JavaScript
 * Handles patient management, filtering, bulk actions, and modal interactions
 */

class PatientListManager {
    constructor() {
        this.selectedPatients = new Set();
        this.init();
    }

    init() {
        this.initEventListeners();
        this.initDataTable();
        this.initModals();
        this.initBulkActions();
    }

    initEventListeners() {
        // Search functionality
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce(this.handleSearch.bind(this), 300));
        }

        // Filter form submission
        const filterForm = document.getElementById('patientFilters');
        if (filterForm) {
            filterForm.addEventListener('change', this.applyFilters.bind(this));
        }

        // Select all checkbox
        const selectAllCheckbox = document.getElementById('selectAll');
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', this.handleSelectAll.bind(this));
        }

        // Individual patient checkboxes
        this.updatePatientCheckboxListeners();
    }

    initDataTable() {
        const table = document.getElementById('patientsTable');
        if (table && typeof $.fn.DataTable !== 'undefined') {
            this.dataTable = $(table).DataTable({
                responsive: true,
                pageLength: 25,
                order: [[5, 'desc']], // Order by registration date
                columnDefs: [
                    { targets: [0, 6], orderable: false }, // Checkbox and actions columns
                    { targets: [0], searchable: false }
                ],
                language: {
                    search: "",
                    searchPlaceholder: "Search patients...",
                    lengthMenu: "Show _MENU_ patients per page",
                    info: "Showing _START_ to _END_ of _TOTAL_ patients",
                    infoEmpty: "No patients found",
                    infoFiltered: "(filtered from _MAX_ total patients)",
                    paginate: {
                        first: "First",
                        last: "Last",
                        next: "Next",
                        previous: "Previous"
                    }
                },
                dom: '<"row"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6"f>>' +
                     '<"row"<"col-sm-12"tr>>' +
                     '<"row"<"col-sm-12 col-md-5"i><"col-sm-12 col-md-7"p>>',
                drawCallback: () => {
                    this.updatePatientCheckboxListeners();
                    this.updateBulkActionsVisibility();
                }
            });
        }
    }

    initModals() {
        // Delete confirmation modal
        this.deleteModal = new bootstrap.Modal(document.getElementById('deletePatientModal'));
        this.bulkDeleteModal = new bootstrap.Modal(document.getElementById('bulkDeleteModal'));

        // Confirm delete button
        const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
        if (confirmDeleteBtn) {
            confirmDeleteBtn.addEventListener('click', this.handlePatientDelete.bind(this));
        }

        // Confirm bulk delete button
        const confirmBulkDeleteBtn = document.getElementById('confirmBulkDeleteBtn');
        if (confirmBulkDeleteBtn) {
            confirmBulkDeleteBtn.addEventListener('click', this.handleBulkDelete.bind(this));
        }
    }

    initBulkActions() {
        // Initialize bulk action visibility
        this.updateBulkActionsVisibility();
    }

    // Event Handlers
    handleSearch(event) {
        const searchTerm = event.target.value.trim();

        if (this.dataTable) {
            this.dataTable.search(searchTerm).draw();
        } else {
            // Fallback: submit form for server-side search
            document.getElementById('patientFilters').submit();
        }
    }

    handleSelectAll(event) {
        const isChecked = event.target.checked;
        const checkboxes = document.querySelectorAll('.patient-checkbox');

        checkboxes.forEach(checkbox => {
            checkbox.checked = isChecked;
            const patientId = checkbox.value;

            if (isChecked) {
                this.selectedPatients.add(patientId);
            } else {
                this.selectedPatients.delete(patientId);
            }
        });

        this.updateBulkActionsVisibility();
        this.updateSelectedCount();
    }

    handlePatientCheckboxChange(event) {
        const checkbox = event.target;
        const patientId = checkbox.value;

        if (checkbox.checked) {
            this.selectedPatients.add(patientId);
        } else {
            this.selectedPatients.delete(patientId);
        }

        this.updateBulkActionsVisibility();
        this.updateSelectedCount();
        this.updateSelectAllCheckbox();
    }

    handlePatientDelete() {
        const patientId = this.deleteModal._element.dataset.patientId;

        if (!patientId) {
            this.showAlert('Error: Patient ID not found', 'error');
            return;
        }

        // Show loading state
        const confirmBtn = document.getElementById('confirmDeleteBtn');
        const originalText = confirmBtn.innerHTML;
        confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Deleting...';
        confirmBtn.disabled = true;

        // Make AJAX request to delete patient
        fetch(`/en/patients/${patientId}/delete/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({ confirm: true })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showAlert('Patient deleted successfully', 'success');
                this.deleteModal.hide();

                // Remove row from table or reload page
                if (this.dataTable) {
                    this.dataTable.ajax.reload();
                } else {
                    location.reload();
                }
            } else {
                throw new Error(data.message || 'Failed to delete patient');
            }
        })
        .catch(error => {
            console.error('Error deleting patient:', error);
            this.showAlert(error.message || 'Failed to delete patient', 'error');
        })
        .finally(() => {
            // Restore button state
            confirmBtn.innerHTML = originalText;
            confirmBtn.disabled = false;
        });
    }

    handleBulkDelete() {
        if (this.selectedPatients.size === 0) {
            this.showAlert('No patients selected', 'warning');
            return;
        }

        const confirmBtn = document.getElementById('confirmBulkDeleteBtn');
        const originalText = confirmBtn.innerHTML;
        confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Deleting...';
        confirmBtn.disabled = true;

        // Make AJAX request for bulk delete
        fetch('/en/patients/bulk-action/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({
                action: 'delete',
                selected_patients: Array.from(this.selectedPatients)
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showAlert(`${data.count} patients deleted successfully`, 'success');
                this.bulkDeleteModal.hide();
                this.selectedPatients.clear();
                this.updateBulkActionsVisibility();

                // Reload table or page
                if (this.dataTable) {
                    this.dataTable.ajax.reload();
                } else {
                    location.reload();
                }
            } else {
                throw new Error(data.message || 'Failed to delete patients');
            }
        })
        .catch(error => {
            console.error('Error deleting patients:', error);
            this.showAlert(error.message || 'Failed to delete patients', 'error');
        })
        .finally(() => {
            confirmBtn.innerHTML = originalText;
            confirmBtn.disabled = false;
        });
    }

    // Utility Methods
    updatePatientCheckboxListeners() {
        const checkboxes = document.querySelectorAll('.patient-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.removeEventListener('change', this.handlePatientCheckboxChange.bind(this));
            checkbox.addEventListener('change', this.handlePatientCheckboxChange.bind(this));
        });
    }

    updateBulkActionsVisibility() {
        const bulkActionsBar = document.getElementById('bulkActionsBar');
        if (bulkActionsBar) {
            if (this.selectedPatients.size > 0) {
                bulkActionsBar.style.display = 'block';
            } else {
                bulkActionsBar.style.display = 'none';
            }
        }
    }

    updateSelectedCount() {
        const selectedCountElement = document.getElementById('selectedCount');
        if (selectedCountElement) {
            selectedCountElement.textContent = this.selectedPatients.size;
        }
    }

    updateSelectAllCheckbox() {
        const selectAllCheckbox = document.getElementById('selectAll');
        const checkboxes = document.querySelectorAll('.patient-checkbox');

        if (selectAllCheckbox && checkboxes.length > 0) {
            const checkedCheckboxes = document.querySelectorAll('.patient-checkbox:checked');
            selectAllCheckbox.checked = checkedCheckboxes.length === checkboxes.length;
            selectAllCheckbox.indeterminate = checkedCheckboxes.length > 0 && checkedCheckboxes.length < checkboxes.length;
        }
    }

    applyFilters() {
        const form = document.getElementById('patientFilters');
        if (form) {
            form.submit();
        }
    }

    resetFilters() {
        const form = document.getElementById('patientFilters');
        if (form) {
            form.reset();
            form.submit();
        }
    }

    exportData(format) {
        const selectedIds = Array.from(this.selectedPatients);
        const params = new URLSearchParams();

        if (selectedIds.length > 0) {
            params.append('selected', selectedIds.join(','));
        }
        params.append('format', format);

        window.open(`/en/patients/export/?${params.toString()}`, '_blank');
    }

    showAlert(message, type = 'info') {
        // Create and show a Bootstrap alert
        const alertContainer = document.getElementById('alertContainer') || this.createAlertContainer();
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        alertContainer.appendChild(alert);

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }

    createAlertContainer() {
        const container = document.createElement('div');
        container.id = 'alertContainer';
        container.className = 'position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
        return container;
    }

    getCSRFToken() {
        return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') ||
               document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    }

    debounce(func, wait) {
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
}

// Global Functions (called from template)
function confirmDeletePatient(patientId, patientName) {
    const modal = document.getElementById('deletePatientModal');
    const nameElement = document.getElementById('deletePatientName');

    if (modal && nameElement) {
        modal.dataset.patientId = patientId;
        nameElement.textContent = patientName;

        const bootstrapModal = bootstrap.Modal.getInstance(modal) || new bootstrap.Modal(modal);
        bootstrapModal.show();
    }
}

function bulkDeleteSelected() {
    const count = patientListManager.selectedPatients.size;
    if (count === 0) {
        patientListManager.showAlert('No patients selected', 'warning');
        return;
    }

    const countElement = document.getElementById('bulkDeleteCount');
    if (countElement) {
        countElement.textContent = count;
    }

    patientListManager.bulkDeleteModal.show();
}

function bulkAction(action) {
    const selectedCount = patientListManager.selectedPatients.size;

    if (selectedCount === 0) {
        patientListManager.showAlert('No patients selected', 'warning');
        return;
    }

    switch (action) {
        case 'delete':
            bulkDeleteSelected();
            break;
        case 'activate':
        case 'deactivate':
            handleBulkStatusChange(action);
            break;
        case 'export':
            patientListManager.exportData('excel');
            break;
        default:
            console.warn('Unknown bulk action:', action);
    }
}

function handleBulkStatusChange(action) {
    const selectedIds = Array.from(patientListManager.selectedPatients);

    fetch('/en/patients/bulk-action/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': patientListManager.getCSRFToken()
        },
        body: JSON.stringify({
            action: action,
            selected_patients: selectedIds
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const actionText = action === 'activate' ? 'activated' : 'deactivated';
            patientListManager.showAlert(`${data.count} patients ${actionText} successfully`, 'success');

            if (patientListManager.dataTable) {
                patientListManager.dataTable.ajax.reload();
            } else {
                location.reload();
            }
        } else {
            throw new Error(data.message || `Failed to ${action} patients`);
        }
    })
    .catch(error => {
        console.error(`Error ${action} patients:`, error);
        patientListManager.showAlert(error.message || `Failed to ${action} patients`, 'error');
    });
}

function resetFilters() {
    patientListManager.resetFilters();
}

function applyFilters() {
    patientListManager.applyFilters();
}

function exportData(format) {
    patientListManager.exportData(format);
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.patientListManager = new PatientListManager();
});
