// Global variables
let selectedPatients = [];
let currentAction = null;

// Helper function to get bulk action URL
function getBulkActionUrl() {
    // Hardcoded for reliability - patients list is always at /en/patients/
    return '/en/patients/bulk-action/';
}

// Initialize when document is ready
$(document).ready(function() {
    initializeDataTable();
    initializeEventListeners();
    initializeSearch();
    initializeTooltips();
    initializeBulkActions();
});

// Initialize DataTable
function initializeDataTable() {
    $('#patientsTable').DataTable({
        responsive: true,
        pageLength: 25,
        lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, "All"]],
        order: [[5, 'desc']], // Sort by registration date by default
        columnDefs: [
            { orderable: false, targets: [0, 6] }, // Disable sorting for checkbox and actions columns
            { responsivePriority: 1, targets: 1 }, // Patient name always visible
            { responsivePriority: 2, targets: 6 }, // Actions always visible
        ],
        language: {
            search: "Quick search:",
            lengthMenu: "Show _MENU_ patients per page",
            info: "Showing _START_ to _END_ of _TOTAL_ patients",
            infoEmpty: "No patients found",
            infoFiltered: "(filtered from _MAX_ total patients)",
            emptyTable: "No patients available in table",
            zeroRecords: "No matching patients found"
        },
        initComplete: function() {
            // Add custom styling to DataTable elements
            $('.dataTables_length select').addClass('filter-input');
            $('.dataTables_filter input').addClass('filter-input');
        }
    });
}

function initializeEventListeners() {
    // Select all checkbox
    $('#selectAll').on('change', function() {
        const isChecked = $(this).is(':checked');
        $('.patient-checkbox').prop('checked', isChecked);
        updateBulkActions();
    });

    // Individual checkboxes
    $(document).on('change', '.patient-checkbox', function() {
        updateBulkActions();
        updateSelectAllState();
    });

    // Search input with debouncing
    let searchTimeout;
    $('#searchInput').on('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(function() {
            $('#patientFilters').submit();
        }, 500);
    });

    // Filter form submission
    $('#patientFilters').on('submit', function(e) {
        e.preventDefault();
        const formData = $(this).serialize();
        updateURL(formData);
        loadPatients(formData);
    });

    // Bulk action buttons
    $('.bulk-buttons .btn').on('click', function() {
        const action = $(this).attr('onclick').match(/'([^']+)'/)[1];
        confirmBulkAction(action);
    });

    // Modal confirm button
    $('#confirmBulkAction').on('click', function() {
        executeBulkAction();
    });
}

function initializeSearch() {
    // Real-time search with debouncing
    const searchInput = document.getElementById('searchInput');
    let searchTimeout;

    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            applyFilters();
        }, 300);
    });
}

function applyFilters() {
    const formData = new FormData(document.getElementById('patientFilters'));
    const params = new URLSearchParams();

    for (let [key, value] of formData.entries()) {
        if (value.trim() !== '') {
            params.append(key, value);
        }
    }

    // Update URL without page reload
    const newUrl = `${window.location.pathname}?${params.toString()}`;
    window.history.pushState({}, '', newUrl);

    // Reload page with new filters
    window.location.reload();
}

function resetFilters() {
    document.getElementById('patientFilters').reset();
    window.location.href = window.location.pathname;
}

function updateBulkActions() {
    const checkedBoxes = document.querySelectorAll('.patient-checkbox:checked');
    const bulkActionsBar = document.getElementById('bulkActionsBar');
    const selectedCount = document.getElementById('selectedCount');

    selectedPatients = Array.from(checkedBoxes).map(cb => cb.value);

    if (selectedPatients.length > 0) {
        bulkActionsBar.classList.add('show');
        selectedCount.textContent = selectedPatients.length;
    } else {
        bulkActionsBar.classList.remove('show');
    }

    updateSelectAllState();
}

function updateSelectAllState() {
    const selectAllCheckbox = document.getElementById('selectAll');
    const allCheckboxes = document.querySelectorAll('.patient-checkbox');
    const checkedBoxes = document.querySelectorAll('.patient-checkbox:checked');

    selectAllCheckbox.checked = allCheckboxes.length > 0 && checkedBoxes.length === allCheckboxes.length;
    selectAllCheckbox.indeterminate = checkedBoxes.length > 0 && checkedBoxes.length < allCheckboxes.length;
}

function bulkAction(action) {
    if (selectedPatients.length === 0) {
        alert('Please select patients first.');
        return;
    }

    currentAction = action;
    const actionMessages = {
        'activate': `Activate ${selectedPatients.length} selected patient(s)?`,
        'deactivate': `Deactivate ${selectedPatients.length} selected patient(s)?`,
        'delete': `Permanently delete ${selectedPatients.length} selected patient(s)? This action cannot be undone.`,
        'export': `Export data for ${selectedPatients.length} selected patient(s)?`
    };

    document.getElementById('bulkActionMessage').textContent = actionMessages[action] || 'Confirm this action?';
    new bootstrap.Modal(document.getElementById('bulkActionModal')).show();
}

function executeBulkAction() {
    if (!currentAction || selectedPatients.length === 0) return;

    const formData = new FormData();
    formData.append('action', currentAction);
    selectedPatients.forEach(id => {
        formData.append('selected_patients', id);
    });

        // send to bulk-action endpoint (robust URL) and include AJAX headers
        const bulkActionUrl = getBulkActionUrl();
        console.log('Bulk action URL:', bulkActionUrl); // Debug logging

        // Validate URL
        if (!bulkActionUrl || !bulkActionUrl.includes('bulk-action')) {
            console.error('Invalid bulk action URL:', bulkActionUrl);
            alert('Error: Invalid bulk action URL. Please refresh the page and try again.');
            return;
        }

        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        const csrfMeta = document.querySelector('meta[name="csrf-token"]');
        const csrfToken = csrfInput ? csrfInput.value : (csrfMeta ? csrfMeta.getAttribute('content') : '');

        fetch(bulkActionUrl, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert('Error: ' + (data.message || 'Unknown error occurred'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while processing your request.');
    });
}

// Patient actions
function viewPatient(patientId) {
    console.log('viewPatient called with:', patientId);
    window.location.href = `/en/patients/${patientId}/`;
}

function editPatient(patientId) {
    console.log('editPatient called with:', patientId);
    window.location.href = `/en/patients/${patientId}/edit/`;
}

function deletePatient(patientId) {
    console.log('deletePatient called with:', patientId);
    if (confirm('Are you sure you want to deactivate this patient? This will hide them from active lists but preserve all medical records.')) {
        console.log('User confirmed, redirecting to:', `/en/patients/${patientId}/delete/`);
        window.location.href = `/en/patients/${patientId}/delete/`;
    } else {
        console.log('User cancelled delete');
    }
}

// Additional utility functions
function initializeTooltips() {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[title]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize tooltips with data-bs-toggle
    const bsTooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    bsTooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

function initializeBulkActions() {
    // Select All functionality
    const selectAllCheckbox = document.getElementById('selectAll');
    const patientCheckboxes = document.querySelectorAll('.patient-checkbox');

    // Select All checkbox handler
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            patientCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateBulkActions();
        });
    }

    // Individual checkbox handlers
    patientCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateBulkActions();
        });
    });
}

function updateURL(formData) {
    const url = new URL(window.location);
    url.search = formData;
    window.history.pushState({}, '', url);
}

function loadPatients(formData) {
    // Show loading
    showLoading();

    $.ajax({
        url: window.location.pathname,
        data: formData,
        type: 'GET',
        success: function(data) {
            // Update the table content
            const tableContainer = $('#patientsTable').closest('.table-responsive');
            const newTable = $(data).find('#patientsTable').closest('.table-responsive').html();
            tableContainer.html(newTable);

            // Reinitialize DataTable
            $('#patientsTable').DataTable().destroy();
            initializeDataTable();
        },
        error: function(xhr, status, error) {
            console.error('Error loading patients:', error);
            alert('Error loading patients. Please try again.');
        },
        complete: function() {
            hideLoading();
        }
    });
}

function showLoading() {
    let loading = document.querySelector('.loading-overlay');
    if (!loading) {
        loading = document.createElement('div');
        loading.className = 'loading-overlay';
        loading.innerHTML = `
            <div class="text-center">
                <div class="loading-spinner mb-3"></div>
                <p>Loading...</p>
            </div>
        `;
        loading.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        document.body.appendChild(loading);
    }
}

function hideLoading() {
    const loading = document.querySelector('.loading-overlay');
    if (loading) {
        loading.remove();
    }
}

function exportData(format) {
    const searchParams = new URLSearchParams(window.location.search);
    searchParams.set('export', format);
    window.location.href = '?' + searchParams.toString();
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        // Show success toast
        const toast = document.createElement('div');
        toast.className = 'toast-container position-fixed top-0 end-0 p-3';
        toast.innerHTML = `
            <div class="toast show" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-body bg-success text-white rounded">
                    <i class="fas fa-check me-2"></i>Patient ID copied to clipboard!
                </div>
            </div>
        `;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }, function(err) {
        console.error('Could not copy text: ', err);
    });
}

// Patient manager for grid/list view switching (if needed)
function patientManager() {
    return {
        currentView: 'grid',
        selectedPatients: [],

        init() {
            // Load view preference from localStorage
            this.currentView = localStorage.getItem('patientViewMode') || 'grid';
            this.setupEventListeners();
        },

        switchView(viewType) {
            this.currentView = viewType;
            localStorage.setItem('patientViewMode', viewType);
        },

        setupEventListeners() {
            // Patient card click handling
            document.addEventListener('click', (e) => {
                const patientCard = e.target.closest('.patient-card, .patient-list-item');
                if (patientCard && !e.target.closest('.btn, .dropdown')) {
                    const patientId = patientCard.dataset.patientId;
                    window.location.href = `/en/patients/${patientId}/`;
                }
            });
        }
    }
}

// Initialize additional functionality
document.addEventListener('DOMContentLoaded', function() {
    // Auto-refresh patient data every 2 minutes (if HTMX is available)
    if (typeof htmx !== 'undefined') {
        setInterval(() => {
            const searchInput = document.querySelector('input[name="q"]');
            if (searchInput && searchInput.value === '') {
                htmx.trigger('#patientsList', 'refresh');
            }
        }, 120000);
    }

    // Initialize patients functionality
    if (typeof initPatients === 'function') {
        initPatients();
    }
});

// Error handling
window.addEventListener('error', function(e) {
    console.error('JavaScript error:', e.error);
    // You could send error reports to your server here
});

window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled promise rejection:', e.reason);
    // Handle unhandled promise rejections
});
