// Communication functionality for appointments
document.addEventListener('DOMContentLoaded', function() {
    console.log('Communication module loaded');

    // Initialize communication features
    initializeCommunicationFeatures();

    function initializeCommunicationFeatures() {
        // Set up bulk communication buttons
        const bulkSmsBtn = document.getElementById('bulkSmsBtn');
        const bulkEmailBtn = document.getElementById('bulkEmailBtn');
        const bulkWhatsAppBtn = document.getElementById('bulkWhatsAppBtn');

        if (bulkSmsBtn) {
            bulkSmsBtn.addEventListener('click', () => openBulkCommunicationModal('sms'));
        }

        if (bulkEmailBtn) {
            bulkEmailBtn.addEventListener('click', () => openBulkCommunicationModal('email'));
        }

        if (bulkWhatsAppBtn) {
            bulkWhatsAppBtn.addEventListener('click', () => openBulkCommunicationModal('whatsapp'));
        }

        // Set up individual communication buttons
        document.querySelectorAll('.communication-btn').forEach(btn => {
            btn.addEventListener('click', handleIndividualCommunication);
        });
    }

    function openBulkCommunicationModal(type) {
        const selectedAppointments = getSelectedAppointments();

        if (selectedAppointments.length === 0) {
            showAlert('Please select at least one appointment', 'warning');
            return;
        }

        // Create and show modal for bulk communication
        const modalHtml = createBulkCommunicationModal(type, selectedAppointments);
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // Initialize modal
        const modal = new bootstrap.Modal(document.getElementById('bulkCommunicationModal'));
        modal.show();

        // Set up form submission
        document.getElementById('sendBulkCommunication').addEventListener('click', () => {
            sendBulkCommunication(type, selectedAppointments);
        });
    }

    function handleIndividualCommunication(event) {
        const btn = event.currentTarget;
        const appointmentId = btn.dataset.appointmentId;
        const communicationType = btn.dataset.type;

        // Open individual communication modal/form
        openIndividualCommunicationModal(appointmentId, communicationType);
    }

    function getSelectedAppointments() {
        const checkboxes = document.querySelectorAll('.appointment-checkbox:checked');
        return Array.from(checkboxes).map(cb => cb.value);
    }

    function createBulkCommunicationModal(type, appointmentIds) {
        const typeLabels = {
            sms: 'SMS',
            email: 'Email',
            whatsapp: 'WhatsApp'
        };

        return `
            <div class="modal fade" id="bulkCommunicationModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Send Bulk ${typeLabels[type]}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p>Send ${typeLabels[type]} to ${appointmentIds.length} selected appointment(s)</p>
                            <div class="mb-3">
                                <label class="form-label">Message</label>
                                <textarea class="form-control" id="bulkMessage" rows="4" placeholder="Enter your message..."></textarea>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Template (Optional)</label>
                                <select class="form-select" id="messageTemplate">
                                    <option value="">Select a template...</option>
                                    <option value="reminder">Appointment Reminder</option>
                                    <option value="confirmation">Appointment Confirmation</option>
                                    <option value="reschedule">Reschedule Notice</option>
                                    <option value="cancellation">Cancellation Notice</option>
                                </select>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="sendBulkCommunication">
                                <i class="fas fa-paper-plane me-2"></i>Send ${typeLabels[type]}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    function sendBulkCommunication(type, appointmentIds) {
        const message = document.getElementById('bulkMessage').value;
        const template = document.getElementById('messageTemplate').value;

        if (!message.trim()) {
            showAlert('Please enter a message', 'error');
            return;
        }

        // Show loading state
        const sendBtn = document.getElementById('sendBulkCommunication');
        const originalText = sendBtn.innerHTML;
        sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Sending...';
        sendBtn.disabled = true;

        // Send AJAX request
        fetch('/appointments/api/bulk-communication/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                type: type,
                appointment_ids: appointmentIds,
                message: message,
                template: template
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert(`Bulk ${type} sent successfully!`, 'success');
                bootstrap.Modal.getInstance(document.getElementById('bulkCommunicationModal')).hide();
                location.reload(); // Refresh to show updated communication status
            } else {
                showAlert(data.error || 'Failed to send communication', 'error');
            }
        })
        .catch(error => {
            console.error('Error sending bulk communication:', error);
            showAlert('An error occurred while sending the communication', 'error');
        })
        .finally(() => {
            sendBtn.innerHTML = originalText;
            sendBtn.disabled = false;
        });
    }

    function openIndividualCommunicationModal(appointmentId, type) {
        // This would open a modal for individual communication
        console.log(`Opening ${type} communication for appointment ${appointmentId}`);
        // Implementation would be similar to bulk but for single appointment
    }

    function getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }

    function showAlert(message, type = 'info') {
        // Use SweetAlert2 if available, otherwise use a simple alert
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
});
