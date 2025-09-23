// Enhanced Appointments Management JavaScript
document.addEventListener('DOMContentLoaded', function() {
    console.log('Enhanced appointments module loaded');

    // Initialize all enhanced features
    initializeEnhancedFeatures();

    function initializeEnhancedFeatures() {
        // Initialize bulk actions
        initializeBulkActions();

        // Initialize advanced filtering
        initializeAdvancedFiltering();

        // Initialize statistics cards
        initializeStatisticsCards();

        // Initialize table enhancements
        initializeTableEnhancements();

        // Initialize export functionality
        initializeExportFeatures();

        // Initialize keyboard shortcuts
        initializeKeyboardShortcuts();
    }

    function initializeBulkActions() {
        const selectAllCheckbox = document.getElementById('selectAllAppointments');
        const appointmentCheckboxes = document.querySelectorAll('.appointment-checkbox');

        // Select all functionality
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', function() {
                appointmentCheckboxes.forEach(cb => {
                    cb.checked = this.checked;
                });
                updateBulkActionButtons();
            });
        }

        // Individual checkbox changes
        appointmentCheckboxes.forEach(cb => {
            cb.addEventListener('change', updateBulkActionButtons);
        });

        // Bulk action buttons
        document.querySelectorAll('.bulk-action-btn').forEach(btn => {
            btn.addEventListener('click', handleBulkAction);
        });
    }

    function updateBulkActionButtons() {
        const selectedCount = document.querySelectorAll('.appointment-checkbox:checked').length;
        const bulkActionButtons = document.querySelectorAll('.bulk-action-btn');

        bulkActionButtons.forEach(btn => {
            btn.disabled = selectedCount === 0;
            const badge = btn.querySelector('.selected-count');
            if (badge) {
                badge.textContent = selectedCount;
            }
        });
    }

    function handleBulkAction(event) {
        const btn = event.currentTarget;
        const action = btn.dataset.action;
        const selectedAppointments = getSelectedAppointmentIds();

        if (selectedAppointments.length === 0) {
            showAlert('Please select at least one appointment', 'warning');
            return;
        }

        switch(action) {
            case 'bulk-complete':
                confirmBulkComplete(selectedAppointments);
                break;
            case 'bulk-cancel':
                confirmBulkCancel(selectedAppointments);
                break;
            case 'bulk-reschedule':
                openBulkRescheduleModal(selectedAppointments);
                break;
            case 'bulk-export':
                exportSelectedAppointments(selectedAppointments);
                break;
            default:
                console.log('Unknown bulk action:', action);
        }
    }

    function initializeAdvancedFiltering() {
        // Date range picker
        const dateRangePicker = document.getElementById('dateRangePicker');
        if (dateRangePicker && typeof flatpickr !== 'undefined') {
            flatpickr(dateRangePicker, {
                mode: 'range',
                dateFormat: 'Y-m-d',
                onChange: function(dates) {
                    if (dates.length === 2) {
                        updateDateFilters(dates[0], dates[1]);
                    }
                }
            });
        }

        // Quick filter buttons
        document.querySelectorAll('.quick-filter-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const filter = this.dataset.filter;
                applyQuickFilter(filter);
            });
        });

        // Clear filters
        const clearFiltersBtn = document.getElementById('clearFiltersBtn');
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', clearAllFilters);
        }
    }

    function initializeStatisticsCards() {
        // Make statistics cards interactive
        document.querySelectorAll('.stat-card').forEach(card => {
            card.addEventListener('click', function() {
                const filter = this.dataset.filter;
                if (filter) {
                    applyQuickFilter(filter);
                }
            });
        });

        // Auto-refresh statistics (optional)
        setInterval(updateStatistics, 300000); // Update every 5 minutes
    }

    function initializeTableEnhancements() {
        // Sortable table headers
        document.querySelectorAll('.sortable-header').forEach(header => {
            header.addEventListener('click', function() {
                const column = this.dataset.column;
                const currentSort = this.dataset.sort;
                const newSort = currentSort === 'asc' ? 'desc' : 'asc';

                sortTable(column, newSort);
            });
        });

        // Row highlighting on hover
        document.querySelectorAll('.appointment-row').forEach(row => {
            row.addEventListener('mouseenter', function() {
                this.classList.add('table-active');
            });
            row.addEventListener('mouseleave', function() {
                this.classList.remove('table-active');
            });
        });

        // Inline editing for quick updates
        initializeInlineEditing();
    }

    function initializeInlineEditing() {
        document.querySelectorAll('.inline-editable').forEach(element => {
            element.addEventListener('dblclick', function() {
                makeEditable(this);
            });
        });
    }

    function makeEditable(element) {
        const originalValue = element.textContent;
        const field = element.dataset.field;
        const appointmentId = element.dataset.appointmentId;

        const input = document.createElement('input');
        input.type = 'text';
        input.value = originalValue;
        input.className = 'form-control form-control-sm';

        element.innerHTML = '';
        element.appendChild(input);
        input.focus();

        input.addEventListener('blur', () => saveInlineEdit(appointmentId, field, input.value, element, originalValue));
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                this.blur();
            } else if (e.key === 'Escape') {
                element.textContent = originalValue;
            }
        });
    }

    function saveInlineEdit(appointmentId, field, value, element, originalValue) {
        if (value === originalValue) {
            element.textContent = originalValue;
            return;
        }

        // Send AJAX request to update
        fetch(`/appointments/api/update/${appointmentId}/`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ [field]: value })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                element.textContent = value;
                showAlert('Updated successfully', 'success');
            } else {
                element.textContent = originalValue;
                showAlert(data.error || 'Update failed', 'error');
            }
        })
        .catch(error => {
            console.error('Error updating field:', error);
            element.textContent = originalValue;
            showAlert('Update failed', 'error');
        });
    }

    function initializeExportFeatures() {
        const exportBtn = document.getElementById('exportBtn');
        if (exportBtn) {
            exportBtn.addEventListener('click', showExportModal);
        }
    }

    function showExportModal() {
        const modalHtml = `
            <div class="modal fade" id="exportModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Export Appointments</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="mb-3">
                                <label class="form-label">Export Format</label>
                                <select class="form-select" id="exportFormat">
                                    <option value="csv">CSV</option>
                                    <option value="excel">Excel</option>
                                    <option value="pdf">PDF</option>
                                </select>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Date Range</label>
                                <input type="text" class="form-control" id="exportDateRange" placeholder="Select date range">
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="startExport">Export</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        const modal = new bootstrap.Modal(document.getElementById('exportModal'));
        modal.show();

        // Initialize date range picker for export
        if (typeof flatpickr !== 'undefined') {
            flatpickr('#exportDateRange', {
                mode: 'range',
                dateFormat: 'Y-m-d'
            });
        }

        document.getElementById('startExport').addEventListener('click', performExport);
    }

    function performExport() {
        const format = document.getElementById('exportFormat').value;
        const dateRange = document.getElementById('exportDateRange').value;

        const url = new URL('/appointments/export/', window.location.origin);
        url.searchParams.set('format', format);
        if (dateRange) {
            url.searchParams.set('date_range', dateRange);
        }

        window.open(url.toString(), '_blank');
        bootstrap.Modal.getInstance(document.getElementById('exportModal')).hide();
    }

    function initializeKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            // Ctrl/Cmd + A to select all
            if ((e.ctrlKey || e.metaKey) && e.key === 'a') {
                e.preventDefault();
                const selectAll = document.getElementById('selectAllAppointments');
                if (selectAll) {
                    selectAll.checked = !selectAll.checked;
                    selectAll.dispatchEvent(new Event('change'));
                }
            }

            // Ctrl/Cmd + F to focus search
            if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
                e.preventDefault();
                const searchInput = document.getElementById('searchInput');
                if (searchInput) {
                    searchInput.focus();
                }
            }
        });
    }

    // Utility functions
    function getSelectedAppointmentIds() {
        return Array.from(document.querySelectorAll('.appointment-checkbox:checked'))
                   .map(cb => cb.value);
    }

    function confirmBulkComplete(appointmentIds) {
        if (confirm(`Mark ${appointmentIds.length} appointment(s) as completed?`)) {
            performBulkAction('complete', appointmentIds);
        }
    }

    function confirmBulkCancel(appointmentIds) {
        const reason = prompt('Enter cancellation reason:');
        if (reason) {
            performBulkAction('cancel', appointmentIds, { reason });
        }
    }

    function performBulkAction(action, appointmentIds, extraData = {}) {
        fetch('/appointments/api/bulk-action/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                action: action,
                appointment_ids: appointmentIds,
                ...extraData
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert(`Bulk ${action} completed successfully`, 'success');
                location.reload();
            } else {
                showAlert(data.error || 'Action failed', 'error');
            }
        })
        .catch(error => {
            console.error('Bulk action error:', error);
            showAlert('An error occurred', 'error');
        });
    }

    function getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }

    function showAlert(message, type = 'info') {
        if (typeof Swal !== 'undefined') {
            Swal.fire({
                icon: type,
                title: message,
                timer: 3000,
                showConfirmButton: false
            });
        } else {
            alert(message);
        }
    }

    function updateStatistics() {
        // Optional: Update statistics cards via AJAX
        console.log('Updating statistics...');
    }

    function applyQuickFilter(filter) {
        // Apply predefined filters
        console.log('Applying quick filter:', filter);
        // Implementation would depend on filter type
    }

    function clearAllFilters() {
        // Clear all active filters
        document.querySelectorAll('.filter-input').forEach(input => {
            input.value = '';
        });
        document.querySelectorAll('.filter-select').forEach(select => {
            select.selectedIndex = 0;
        });
        // Submit form or trigger AJAX reload
    }

    function sortTable(column, direction) {
        // Implement table sorting
        console.log('Sorting by:', column, direction);
    }

    function updateDateFilters(startDate, endDate) {
        // Update date filter inputs
        console.log('Date range:', startDate, endDate);
    }

    function exportSelectedAppointments(appointmentIds) {
        // Export selected appointments
        console.log('Exporting appointments:', appointmentIds);
    }

    function openBulkRescheduleModal(appointmentIds) {
        // Open modal for bulk rescheduling
        console.log('Bulk reschedule:', appointmentIds);
    }
});
