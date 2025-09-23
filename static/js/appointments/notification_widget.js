document.addEventListener('DOMContentLoaded', function() {
    const appointmentId = '{{ appointment.id }}';

    // Load notification status on page load
    loadNotificationStatus();

    // Individual notification button handlers
    document.querySelectorAll('.notification-btn').forEach(button => {
        button.addEventListener('click', function() {
            const notificationType = this.dataset.type;
            sendSingleNotification(notificationType, this);
        });
    });

    // Bulk notification handler
    document.getElementById('sendBulkNotifications').addEventListener('click', function() {
        sendBulkNotifications(this);
    });

    // Auto-check available notification types
    document.addEventListener('notificationStatusLoaded', function(event) {
        const availableContacts = event.detail.availableContacts;

        // Update bulk checkboxes based on available contacts
        document.getElementById('bulkEmail').disabled = !availableContacts.email;
        document.getElementById('bulkWhatsApp').disabled = !availableContacts.whatsapp;
        document.getElementById('bulkTelegram').disabled = !availableContacts.telegram;
        document.getElementById('bulkViber').disabled = !availableContacts.viber;
    });

    function loadNotificationStatus() {
        fetch(`/appointments/${appointmentId}/notifications/status/`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateNotificationStatus(data);

                    // Dispatch custom event
                    const event = new CustomEvent('notificationStatusLoaded', {
                        detail: data
                    });
                    document.dispatchEvent(event);
                } else {
                    showNotificationError('Failed to load notification status');
                }
            })
            .catch(error => {
                console.error('Error loading notification status:', error);
                showNotificationError('Error loading notification status');
            });
    }

    function updateNotificationStatus(data) {
        const statusEl = document.getElementById('notificationStatus');
        const availableContacts = data.available_contacts;

        // Update contact information
        const emailEl = document.getElementById('patientEmail');
        const phoneEl = document.getElementById('patientPhone');

        if (data.patient_email) {
            emailEl.innerHTML = `<span class="contact-value available">${data.patient_email}</span>`;
        } else {
            emailEl.innerHTML = `<span class="contact-value unavailable">No email address</span>`;
        }

        if (data.patient_phone) {
            phoneEl.innerHTML = `<span class="contact-value available">${data.patient_phone}</span>`;
        } else {
            phoneEl.innerHTML = `<span class="contact-value unavailable">No phone number</span>`;
        }

        // Update notification status
        if (data.notification_sent) {
            statusEl.innerHTML = `
                <div class="notification-status sent">
                    <i class="bi bi-check-circle-fill"></i>
                    Notifications have been sent
                </div>
            `;
        } else {
            statusEl.innerHTML = `
                <div class="notification-status not-sent">
                    <i class="bi bi-exclamation-circle-fill"></i>
                    No notifications sent yet
                </div>
            `;
        }

        // Update button states
        document.querySelectorAll('.notification-btn').forEach(button => {
            const type = button.dataset.type;
            const isAvailable = availableContacts[type];

            if (!isAvailable) {
                button.disabled = true;
                button.classList.add('disabled');
                button.title = `No ${type} contact available`;
            }
        });

        // Update notification history
        updateNotificationHistory(data.notification_history || []);
    }

    function updateNotificationHistory(history) {
        const historyEl = document.getElementById('historyContent');

        if (history.length === 0) {
            historyEl.innerHTML = '<div class="text-muted">No notification history available</div>';
            return;
        }

        const historyHtml = history.map(item => `
            <div class="history-item ${item.type}">
                <div class="icon">
                    ${getNotificationIcon(item.type)}
                </div>
                <div class="flex-grow-1">
                    <strong>${item.type.charAt(0).toUpperCase() + item.type.slice(1)}</strong>
                    <span class="text-muted ms-2">
                        ${item.sent ? 'Sent' : 'Failed'}
                        ${item.sent_at ? ' - ' + new Date(item.sent_at).toLocaleString() : ''}
                    </span>
                </div>
            </div>
        `).join('');

        historyEl.innerHTML = historyHtml;
    }

    function getNotificationIcon(type) {
        const icons = {
            'email': '<i class="bi bi-envelope"></i>',
            'whatsapp': '<i class="bi bi-whatsapp"></i>',
            'telegram': '<i class="bi bi-telegram"></i>',
            'viber': '<i class="bi bi-chat-dots"></i>'
        };
        return icons[type] || '<i class="bi bi-bell"></i>';
    }

    function sendSingleNotification(type, button) {
        // Show loading state
        button.disabled = true;
        button.querySelector('.btn-text').style.display = 'none';
        button.querySelector('.btn-spinner').classList.remove('d-none');

        const formData = new FormData();
        formData.append('notification_type', type);

        fetch(`/appointments/${appointmentId}/notifications/send/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCsrfToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotificationSuccess(data.message);
                button.classList.add('sent');
                button.innerHTML = `<i class="bi bi-check-circle-fill me-1"></i>Sent`;

                // Reload status to update history
                setTimeout(loadNotificationStatus, 1000);
            } else {
                showNotificationError(data.message);
                resetButton(button, type);
            }
        })
        .catch(error => {
            console.error('Error sending notification:', error);
            showNotificationError('Error sending notification');
            resetButton(button, type);
        });
    }

    function sendBulkNotifications(button) {
        const selectedTypes = [];
        document.querySelectorAll('.bulk-notifications input[type="checkbox"]:checked').forEach(checkbox => {
            selectedTypes.push(checkbox.value);
        });

        if (selectedTypes.length === 0) {
            showNotificationError('Please select at least one notification type');
            return;
        }

        // Show loading state
        button.disabled = true;
        document.getElementById('bulkSpinner').classList.remove('d-none');

        const formData = new FormData();
        selectedTypes.forEach(type => {
            formData.append('notification_types[]', type);
        });

        fetch(`/appointments/${appointmentId}/notifications/send-bulk/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCsrfToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotificationSuccess(data.message);

                // Update individual button states
                Object.entries(data.results).forEach(([type, success]) => {
                    const btn = document.querySelector(`.notification-btn[data-type="${type}"]`);
                    if (btn && success) {
                        btn.classList.add('sent');
                        btn.innerHTML = `<i class="bi bi-check-circle-fill me-1"></i>Sent`;
                    }
                });

                // Reload status
                setTimeout(loadNotificationStatus, 1000);
            } else {
                showNotificationError(data.message || 'Failed to send notifications');
            }
        })
        .catch(error => {
            console.error('Error sending bulk notifications:', error);
            showNotificationError('Error sending notifications');
        })
        .finally(() => {
            button.disabled = false;
            document.getElementById('bulkSpinner').classList.add('d-none');

            // Uncheck all boxes
            document.querySelectorAll('.bulk-notifications input[type="checkbox"]').forEach(checkbox => {
                checkbox.checked = false;
            });
        });
    }

    function resetButton(button, type) {
        button.disabled = false;
        button.querySelector('.btn-text').style.display = 'inline';
        button.querySelector('.btn-spinner').classList.add('d-none');
    }

    function showNotificationSuccess(message) {
        // You can integrate with your existing notification system here
        console.log('Success:', message);

        // Simple toast notification
        const toast = document.createElement('div');
        toast.className = 'toast-notification success';
        toast.innerHTML = `<i class="bi bi-check-circle-fill me-2"></i>${message}`;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.classList.add('show');
        }, 100);

        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => document.body.removeChild(toast), 300);
        }, 3000);
    }

    function showNotificationError(message) {
        // You can integrate with your existing notification system here
        console.error('Error:', message);

        // Simple toast notification
        const toast = document.createElement('div');
        toast.className = 'toast-notification error';
        toast.innerHTML = `<i class="bi bi-exclamation-circle-fill me-2"></i>${message}`;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.classList.add('show');
        }, 100);

        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => document.body.removeChild(toast), 300);
        }, 3000);
    }

    function getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }
});
