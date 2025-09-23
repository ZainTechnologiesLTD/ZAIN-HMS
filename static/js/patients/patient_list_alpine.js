/**
 * Alpine.js + HTMX Patient List Manager
 * Modern reactive approach using Alpine.js for state and HTMX for server interactions
 */

// Global Alpine.js configuration for patient management
document.addEventListener('alpine:init', () => {
    Alpine.data('patientManager', () => ({
        // Reactive State
        searchQuery: '',
        filters: {
            gender: '',
            blood_group: '',
            is_vip: ''
        },
        selectedPatients: [],
        selectAll: false,

        // Modal State
        showDeleteModal: false,
        showBulkDeleteModal: false,

        // Delete State
        deletePatientId: null,
        deletePatientName: '',
        isDeleting: false,
        isBulkDeleting: false,

        // Watchers
        init() {
            // Watch for changes in selectedPatients to update selectAll
            this.$watch('selectedPatients', () => {
                const checkboxes = document.querySelectorAll('input[type="checkbox"][value]');
                this.selectAll = checkboxes.length > 0 && this.selectedPatients.length === checkboxes.length;
            });

            // Set up HTMX error handling
            document.body.addEventListener('htmx:responseError', (event) => {
                this.showErrorMessage('Server error occurred. Please try again.');
                this.isDeleting = false;
                this.isBulkDeleting = false;
            });

            // Set up HTMX success handling
            document.body.addEventListener('htmx:afterRequest', (event) => {
                if (event.detail.successful && event.detail.xhr.status === 200) {
                    // Clear selections after successful operations
                    if (event.detail.pathInfo.path.includes('delete') ||
                        event.detail.pathInfo.path.includes('bulk')) {
                        this.selectedPatients = [];
                        this.selectAll = false;
                    }
                }
            });
        },

        // Selection Methods
        toggleSelectAll() {
            if (this.selectAll) {
                const checkboxes = document.querySelectorAll('input[type="checkbox"][value]');
                this.selectedPatients = Array.from(checkboxes).map(cb => cb.value);
            } else {
                this.selectedPatients = [];
            }
        },

        // Delete Methods
        confirmDelete(patientId, patientName) {
            this.deletePatientId = patientId;
            this.deletePatientName = patientName;
            this.showDeleteModal = true;
        },

        async deletePatient() {
            if (!this.deletePatientId) return;

            this.isDeleting = true;

            try {
                const response = await htmx.ajax('POST', `/en/patients/${this.deletePatientId}/delete/`, {
                    headers: {
                        'X-CSRFToken': this.getCSRFToken(),
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ confirm: 'yes' })
                });

                if (response.ok) {
                    // Refresh the patient table
                    htmx.trigger('#patient-table-container', 'refresh');
                    this.closeDeleteModal();
                    this.showSuccessMessage('Patient deleted successfully');
                } else {
                    throw new Error('Delete failed');
                }
            } catch (error) {
                this.showErrorMessage('Failed to delete patient');
                console.error('Delete error:', error);
            } finally {
                this.isDeleting = false;
            }
        },

        closeDeleteModal() {
            this.showDeleteModal = false;
            this.deletePatientId = null;
            this.deletePatientName = '';
        },

        // Bulk Actions
        async bulkAction(action) {
            if (this.selectedPatients.length === 0) {
                this.showErrorMessage('Please select at least one patient');
                return;
            }

            if (action === 'delete') {
                this.showBulkDeleteModal = true;
                return;
            }

            try {
                const formData = new FormData();
                formData.append('action', action);
                this.selectedPatients.forEach(id => {
                    formData.append('patient_ids', id);
                });

                await htmx.ajax('POST', '/en/patients/bulk-action/', {
                    headers: {
                        'X-CSRFToken': this.getCSRFToken()
                    },
                    body: formData
                });

                htmx.trigger('#patient-table-container', 'refresh');
                this.selectedPatients = [];
                this.selectAll = false;
                this.showSuccessMessage(`Bulk ${action} completed successfully`);
            } catch (error) {
                this.showErrorMessage(`Failed to perform bulk ${action}`);
                console.error('Bulk action error:', error);
            }
        },

        async bulkDelete() {
            this.isBulkDeleting = true;

            try {
                const formData = new FormData();
                formData.append('action', 'delete');
                this.selectedPatients.forEach(id => {
                    formData.append('patient_ids', id);
                });

                await htmx.ajax('POST', '/en/patients/bulk-action/', {
                    headers: {
                        'X-CSRFToken': this.getCSRFToken()
                    },
                    body: formData
                });

                htmx.trigger('#patient-table-container', 'refresh');
                this.selectedPatients = [];
                this.selectAll = false;
                this.showBulkDeleteModal = false;
                this.showSuccessMessage('Selected patients deleted successfully');
            } catch (error) {
                this.showErrorMessage('Failed to delete selected patients');
                console.error('Bulk delete error:', error);
            } finally {
                this.isBulkDeleting = false;
            }
        },

        closeBulkDeleteModal() {
            this.showBulkDeleteModal = false;
        },

        // Filter Methods
        resetFilters() {
            this.searchQuery = '';
            this.filters = {
                gender: '',
                blood_group: '',
                is_vip: ''
            };

            // Clear form inputs
            const form = document.querySelector('#patient-filters-form');
            if (form) {
                form.reset();
            }

            // Trigger HTMX reload
            htmx.trigger('#patient-table-container', 'refresh');
        },

        // Export Methods
        exportData(format) {
            const params = new URLSearchParams();
            if (this.searchQuery) params.append('q', this.searchQuery);
            if (this.filters.gender) params.append('gender', this.filters.gender);
            if (this.filters.blood_group) params.append('blood_group', this.filters.blood_group);
            if (this.filters.is_vip) params.append('is_vip', this.filters.is_vip);
            params.append('export', format);

            if (this.selectedPatients.length > 0) {
                this.selectedPatients.forEach(id => {
                    params.append('selected_patients', id);
                });
            }

            window.location.href = `/en/patients/?${params.toString()}`;
        },

        // Utility Methods
        getCSRFToken() {
            return document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                   document.querySelector('meta[name=csrf-token]')?.content ||
                   '';
        },

        showSuccessMessage(message) {
            this.showToast('success', message);
        },

        showErrorMessage(message) {
            this.showToast('error', message);
        },

        showToast(type, message) {
            const toast = document.createElement('div');
            toast.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible position-fixed`;
            toast.style.cssText = 'top: 20px; right: 20px; z-index: 1060; min-width: 300px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);';
            toast.innerHTML = `
                <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} me-2"></i>
                ${message}
                <button type="button" class="btn-close" onclick="this.parentElement.remove()" aria-label="Close"></button>
            `;
            document.body.appendChild(toast);

            // Auto-remove after 5 seconds
            setTimeout(() => {
                if (toast.parentElement) {
                    toast.remove();
                }
            }, 5000);
        },

        // Computed Properties
        get hasSelectedPatients() {
            return this.selectedPatients.length > 0;
        },

        get selectedCount() {
            return this.selectedPatients.length;
        }
    }));
});

// HTMX Configuration for Patient Management
document.addEventListener('DOMContentLoaded', function() {
    // Configure HTMX defaults for patient management
    htmx.config.useTemplateFragments = true;
    htmx.config.refreshOnHistoryMiss = true;

    // Global HTMX event handlers
    document.body.addEventListener('htmx:configRequest', function(event) {
        // Add CSRF token to all HTMX requests
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                         document.querySelector('meta[name=csrf-token]')?.content;
        if (csrfToken) {
            event.detail.headers['X-CSRFToken'] = csrfToken;
        }
    });

    document.body.addEventListener('htmx:beforeRequest', function(event) {
        // Show loading indicators
        const indicator = document.querySelector('#loading-indicator');
        if (indicator) {
            indicator.style.display = 'block';
        }
    });

    document.body.addEventListener('htmx:afterRequest', function(event) {
        // Hide loading indicators
        const indicator = document.querySelector('#loading-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }

        // Handle errors
        if (!event.detail.successful) {
            console.error('HTMX request failed:', event.detail);
        }
    });
});
