function checkInAppointment() {
    const modal = new bootstrap.Modal(document.getElementById('checkInModal'));
    modal.show();
}

function confirmCheckIn() {
    fetch(`{% url 'appointments:appointment_detail' appointment.id %}checkin/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            bootstrap.Modal.getInstance(document.getElementById('checkInModal')).hide();
            showAlert('Patient checked in successfully!', 'success');
            setTimeout(() => location.reload(), 1500);
        } else {
            showAlert(data.message || 'Error checking in patient', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error checking in patient', 'error');
    });
}

function startConsultation() {
    if (confirm('Start consultation for this appointment?')) {
        fetch(`{% url 'appointments:appointment_detail' appointment.id %}start/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('Consultation started!', 'success');
                setTimeout(() => location.reload(), 1500);
            } else {
                showAlert(data.message || 'Error starting consultation', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Error starting consultation', 'error');
        });
    }
}

function completeAppointment() {
    if (confirm('Mark this appointment as completed?')) {
        fetch(`{% url 'appointments:appointment_detail' appointment.id %}complete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('Appointment completed!', 'success');
                setTimeout(() => location.reload(), 1500);
            } else {
                showAlert(data.message || 'Error completing appointment', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Error completing appointment', 'error');
        });
    }
}

function cancelAppointment() {
    const modal = new bootstrap.Modal(document.getElementById('cancelModal'));
    modal.show();
}

function confirmCancel() {
    const reason = document.getElementById('cancellationReason').value.trim();
    const notifyPatient = document.getElementById('notifyPatient').checked;

    if (!reason) {
        showAlert('Please provide a reason for cancellation', 'warning');
        return;
    }

    fetch(`{% url 'appointments:appointment_detail' appointment.id %}cancel/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            cancellation_reason: reason,
            notify_patient: notifyPatient
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            bootstrap.Modal.getInstance(document.getElementById('cancelModal')).hide();
            showAlert('Appointment cancelled successfully!', 'success');
            setTimeout(() => location.reload(), 1500);
        } else {
            showAlert(data.message || 'Error cancelling appointment', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error cancelling appointment', 'error');
    });
}

function rescheduleAppointment() {
    const modal = new bootstrap.Modal(document.getElementById('rescheduleModal'));
    modal.show();

    // Set minimum date to today
    document.getElementById('newDate').min = new Date().toISOString().split('T')[0];

    // Load available time slots when date changes
    document.getElementById('newDate').addEventListener('change', function() {
        loadAvailableSlots(this.value);
    });
}

function loadAvailableSlots(date) {
    const timeSelect = document.getElementById('newTime');
    timeSelect.innerHTML = '<option value="">Loading...</option>';

    fetch(`{% url 'appointments:get_available_time_slots' %}?doctor_id={{ appointment.doctor.id }}&date=${date}&exclude={{ appointment.id }}`)
        .then(response => response.json())
        .then(data => {
            timeSelect.innerHTML = '<option value="">Select time</option>';
            data.slots.forEach(slot => {
                if (slot.available) {
                    const option = document.createElement('option');
                    option.value = slot.time;
                    option.textContent = slot.time;
                    timeSelect.appendChild(option);
                }
            });
        })
        .catch(error => {
            console.error('Error:', error);
            timeSelect.innerHTML = '<option value="">Error loading slots</option>';
        });
}

function confirmReschedule() {
    const newDate = document.getElementById('newDate').value;
    const newTime = document.getElementById('newTime').value;
    const reason = document.getElementById('rescheduleReason').value;

    if (!newDate || !newTime) {
        showAlert('Please select both date and time', 'warning');
        return;
    }

    fetch(`{% url 'appointments:appointment_detail' appointment.id %}reschedule/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            new_date: newDate,
            new_time: newTime,
            reschedule_reason: reason
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            bootstrap.Modal.getInstance(document.getElementById('rescheduleModal')).hide();
            showAlert('Appointment rescheduled successfully!', 'success');
            setTimeout(() => location.reload(), 1500);
        } else {
            showAlert(data.message || 'Error rescheduling appointment', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error rescheduling appointment', 'error');
    });
}

function printAppointment() {
    window.print();
}

function scrollToNotifications() {
    // Scroll to the notification widget
    const notificationWidget = document.querySelector('.card .card-header h6:contains("Patient Notifications")');
    if (notificationWidget) {
        notificationWidget.closest('.card').scrollIntoView({
            behavior: 'smooth',
            block: 'center'
        });

        // Add a highlight effect
        const card = notificationWidget.closest('.card');
        card.style.boxShadow = '0 0 20px rgba(0, 123, 255, 0.3)';
        setTimeout(() => {
            card.style.boxShadow = '';
        }, 2000);
    }
}

function exportToPDF() {
    window.open(`{% url 'appointments:appointment_detail' appointment.id %}export/pdf/`, '_blank');
}

function showAlert(message, type = 'info') {
    // Create a toast notification
    const toastContainer = document.getElementById('toastContainer') || createToastContainer();

    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-bg-${type === 'error' ? 'danger' : type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;

    toastContainer.appendChild(toast);

    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();

    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}
