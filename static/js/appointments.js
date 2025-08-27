/* ZAIN HMS - Appointments Module JavaScript */

// Appointments Manager
function initAppointments() {
    console.log('Appointments module initialized');
    
    // Setup appointments functionality
    setupAppointmentActions();
    setupCalendarView();
    setupFilters();
    setupRealTimeUpdates();
}

function setupAppointmentActions() {
    // Mark appointment as completed
    document.querySelectorAll('[data-action="mark-completed"]').forEach(btn => {
        btn.addEventListener('click', function() {
            const appointmentId = this.dataset.appointmentId;
            markCompleted(appointmentId);
        });
    });
    
    // Cancel appointment
    document.querySelectorAll('[data-action="cancel-appointment"]').forEach(btn => {
        btn.addEventListener('click', function() {
            const appointmentId = this.dataset.appointmentId;
            cancelAppointment(appointmentId);
        });
    });
    
    // Reschedule appointment
    document.querySelectorAll('[data-action="reschedule"]').forEach(btn => {
        btn.addEventListener('click', function() {
            const appointmentId = this.dataset.appointmentId;
            rescheduleAppointment(appointmentId);
        });
    });
    
    // View appointment details
    document.querySelectorAll('[data-action="view-details"]').forEach(btn => {
        btn.addEventListener('click', function() {
            const appointmentId = this.dataset.appointmentId;
            viewAppointmentDetails(appointmentId);
        });
    });
}

function setupCalendarView() {
    // Calendar navigation
    document.querySelectorAll('.calendar-nav').forEach(nav => {
        nav.addEventListener('click', function() {
            const direction = this.dataset.direction;
            const currentDate = this.dataset.currentDate;
            navigateCalendar(direction, currentDate);
        });
    });
    
    // Time slot selection
    document.querySelectorAll('.time-slot').forEach(slot => {
        slot.addEventListener('click', function() {
            if (!this.classList.contains('occupied')) {
                selectTimeSlot(this);
            }
        });
    });
}

function setupFilters() {
    const filterForm = document.querySelector('.appointment-filters form');
    if (filterForm) {
        // Auto-submit on filter change
        const selects = filterForm.querySelectorAll('select');
        selects.forEach(select => {
            select.addEventListener('change', function() {
                filterForm.submit();
            });
        });
        
        // Add loading state on submit
        filterForm.addEventListener('submit', function() {
            const submitBtn = this.querySelector('[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Filtering...';
            }
        });
    }
}

function setupRealTimeUpdates() {
    // Update appointment statuses every 30 seconds
    setInterval(() => {
        updateAppointmentStatuses();
    }, 30000);
    
    // Check for upcoming appointments every 5 minutes
    setInterval(() => {
        checkUpcomingAppointments();
    }, 300000);
}

// Appointment Functions
function markCompleted(appointmentId) {
    if (confirm('Mark this appointment as completed?')) {
        updateAppointmentStatus(appointmentId, 'COMPLETED');
    }
}

function cancelAppointment(appointmentId) {
    if (confirm('Are you sure you want to cancel this appointment?')) {
        updateAppointmentStatus(appointmentId, 'CANCELLED');
    }
}

function updateAppointmentStatus(appointmentId, status) {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    
    fetch(`/appointments/${appointmentId}/update-status/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: status })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(`Appointment ${status.toLowerCase()} successfully`, 'success');
            location.reload();
        } else {
            showNotification(data.message || 'Failed to update appointment', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred while updating appointment', 'error');
    });
}

function rescheduleAppointment(appointmentId) {
    console.log('Rescheduling appointment:', appointmentId);
    
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Reschedule Appointment</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <form id="reschedule-form">
                        <input type="hidden" name="appointment_id" value="${appointmentId}">
                        <div class="mb-3">
                            <label class="form-label">New Date</label>
                            <input type="date" class="form-control" name="new_date" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">New Time</label>
                            <select class="form-select" name="new_time" required>
                                <option value="">Select time...</option>
                                <option value="09:00">09:00 AM</option>
                                <option value="09:30">09:30 AM</option>
                                <option value="10:00">10:00 AM</option>
                                <option value="10:30">10:30 AM</option>
                                <option value="11:00">11:00 AM</option>
                                <option value="11:30">11:30 AM</option>
                                <option value="14:00">02:00 PM</option>
                                <option value="14:30">02:30 PM</option>
                                <option value="15:00">03:00 PM</option>
                                <option value="15:30">03:30 PM</option>
                                <option value="16:00">04:00 PM</option>
                                <option value="16:30">04:30 PM</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Reason for Reschedule</label>
                            <textarea class="form-control" name="reason" rows="3" placeholder="Optional reason..."></textarea>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-primary" onclick="submitReschedule()">Reschedule</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    // Set minimum date to today
    const dateInput = modal.querySelector('[name="new_date"]');
    const today = new Date().toISOString().split('T')[0];
    dateInput.min = today;
    
    // Clean up when modal is hidden
    modal.addEventListener('hidden.bs.modal', function() {
        document.body.removeChild(modal);
    });
}

function submitReschedule() {
    const form = document.getElementById('reschedule-form');
    const formData = new FormData(form);
    
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    if (csrfToken) {
        formData.append('csrfmiddlewaretoken', csrfToken);
    }
    
    fetch('/appointments/reschedule/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Appointment rescheduled successfully', 'success');
            location.reload();
        } else {
            showNotification(data.message || 'Failed to reschedule appointment', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred while rescheduling appointment', 'error');
    });
}

function viewAppointmentDetails(appointmentId) {
    console.log('Viewing appointment details:', appointmentId);
    
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Appointment Details</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="text-center">
                        <div class="spinner-border" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    // Load appointment details
    fetch(`/appointments/${appointmentId}/details/`)
        .then(response => response.json())
        .then(data => {
            const modalBody = modal.querySelector('.modal-body');
            modalBody.innerHTML = `
                <div class="row">
                    <div class="col-md-6">
                        <h6>Patient Information</h6>
                        <p><strong>Name:</strong> ${data.patient.name}</p>
                        <p><strong>ID:</strong> ${data.patient.id}</p>
                        <p><strong>Phone:</strong> ${data.patient.phone}</p>
                        <p><strong>Email:</strong> ${data.patient.email}</p>
                    </div>
                    <div class="col-md-6">
                        <h6>Appointment Details</h6>
                        <p><strong>Date:</strong> ${data.appointment_date}</p>
                        <p><strong>Time:</strong> ${data.appointment_time}</p>
                        <p><strong>Doctor:</strong> Dr. ${data.doctor.name}</p>
                        <p><strong>Department:</strong> ${data.department}</p>
                        <p><strong>Status:</strong> <span class="badge bg-${getStatusColor(data.status)}">${data.status}</span></p>
                    </div>
                </div>
                ${data.reason ? `
                    <div class="row mt-3">
                        <div class="col-12">
                            <h6>Reason for Visit</h6>
                            <p>${data.reason}</p>
                        </div>
                    </div>
                ` : ''}
                ${data.notes ? `
                    <div class="row mt-3">
                        <div class="col-12">
                            <h6>Notes</h6>
                            <p>${data.notes}</p>
                        </div>
                    </div>
                ` : ''}
            `;
        })
        .catch(error => {
            console.error('Error loading appointment details:', error);
            modal.querySelector('.modal-body').innerHTML = '<p class="text-danger">Error loading appointment details</p>';
        });
    
    // Clean up when modal is hidden
    modal.addEventListener('hidden.bs.modal', function() {
        document.body.removeChild(modal);
    });
}

// Calendar Functions
function navigateCalendar(direction, currentDate) {
    const url = new URL(window.location);
    const date = new Date(currentDate);
    
    if (direction === 'prev') {
        date.setDate(date.getDate() - 7);
    } else if (direction === 'next') {
        date.setDate(date.getDate() + 7);
    }
    
    url.searchParams.set('date', date.toISOString().split('T')[0]);
    window.location.href = url.toString();
}

function selectTimeSlot(slotElement) {
    // Remove selection from other slots
    document.querySelectorAll('.time-slot.selected').forEach(slot => {
        slot.classList.remove('selected');
    });
    
    // Select current slot
    slotElement.classList.add('selected');
    
    // Get slot data
    const date = slotElement.dataset.date;
    const time = slotElement.dataset.time;
    const doctorId = slotElement.dataset.doctorId;
    
    // Enable book appointment button or trigger booking modal
    showBookingModal(date, time, doctorId);
}

function showBookingModal(date, time, doctorId) {
    console.log('Booking appointment for:', { date, time, doctorId });
    
    // Create booking modal
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Book Appointment</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <form id="booking-form">
                        <input type="hidden" name="date" value="${date}">
                        <input type="hidden" name="time" value="${time}">
                        <input type="hidden" name="doctor_id" value="${doctorId}">
                        
                        <div class="mb-3">
                            <label class="form-label">Patient</label>
                            <select class="form-select" name="patient_id" required>
                                <option value="">Select patient...</option>
                                <!-- Patients will be loaded dynamically -->
                            </select>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Appointment Type</label>
                            <select class="form-select" name="appointment_type" required>
                                <option value="">Select type...</option>
                                <option value="CONSULTATION">Consultation</option>
                                <option value="FOLLOW_UP">Follow-up</option>
                                <option value="EMERGENCY">Emergency</option>
                                <option value="ROUTINE_CHECKUP">Routine Checkup</option>
                            </select>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Reason for Visit</label>
                            <textarea class="form-control" name="reason" rows="3" placeholder="Brief description of the reason for visit..."></textarea>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Priority</label>
                            <select class="form-select" name="priority">
                                <option value="NORMAL">Normal</option>
                                <option value="URGENT">Urgent</option>
                                <option value="EMERGENCY">Emergency</option>
                            </select>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-primary" onclick="submitBooking()">Book Appointment</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    // Load patients for selection
    loadPatientsForBooking(modal);
    
    // Clean up when modal is hidden
    modal.addEventListener('hidden.bs.modal', function() {
        document.body.removeChild(modal);
    });
}

function loadPatientsForBooking(modal) {
    const patientSelect = modal.querySelector('[name="patient_id"]');
    
    fetch('/api/patients/')
        .then(response => response.json())
        .then(data => {
            data.patients.forEach(patient => {
                const option = document.createElement('option');
                option.value = patient.id;
                option.textContent = `${patient.name} (${patient.patient_id})`;
                patientSelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error loading patients:', error);
        });
}

function submitBooking() {
    const form = document.getElementById('booking-form');
    const formData = new FormData(form);
    
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    if (csrfToken) {
        formData.append('csrfmiddlewaretoken', csrfToken);
    }
    
    fetch('/appointments/book/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Appointment booked successfully', 'success');
            location.reload();
        } else {
            showNotification(data.message || 'Failed to book appointment', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred while booking appointment', 'error');
    });
}

// Real-time Update Functions
function updateAppointmentStatuses() {
    const appointmentCards = document.querySelectorAll('[data-appointment-id]');
    const appointmentIds = Array.from(appointmentCards).map(card => card.dataset.appointmentId);
    
    if (appointmentIds.length > 0) {
        fetch('/appointments/api/statuses/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value
            },
            body: JSON.stringify({ appointment_ids: appointmentIds })
        })
        .then(response => response.json())
        .then(data => {
            data.appointments.forEach(appointment => {
                updateAppointmentCardStatus(appointment.id, appointment.status);
            });
        })
        .catch(error => {
            console.error('Error updating appointment statuses:', error);
        });
    }
}

function updateAppointmentCardStatus(appointmentId, status) {
    const card = document.querySelector(`[data-appointment-id="${appointmentId}"]`);
    if (card) {
        const statusElement = card.querySelector('.appointment-status');
        if (statusElement) {
            statusElement.textContent = status;
            statusElement.className = `appointment-status status-${status.toLowerCase()}`;
        }
    }
}

function checkUpcomingAppointments() {
    fetch('/appointments/api/upcoming/')
        .then(response => response.json())
        .then(data => {
            if (data.upcoming_appointments.length > 0) {
                data.upcoming_appointments.forEach(appointment => {
                    if (appointment.minutes_until <= 15) {
                        showUpcomingAppointmentNotification(appointment);
                    }
                });
            }
        })
        .catch(error => {
            console.error('Error checking upcoming appointments:', error);
        });
}

function showUpcomingAppointmentNotification(appointment) {
    showNotification(
        `Upcoming: ${appointment.patient_name} with Dr. ${appointment.doctor_name} in ${appointment.minutes_until} minutes`,
        'info',
        0 // Don't auto-hide
    );
}

// Helper Functions
function getStatusColor(status) {
    const colors = {
        'SCHEDULED': 'primary',
        'COMPLETED': 'success',
        'CANCELLED': 'danger',
        'PENDING': 'warning',
        'RESCHEDULED': 'info'
    };
    return colors[status] || 'secondary';
}

// Search and Filter Functions
function searchAppointments(query) {
    const appointmentCards = document.querySelectorAll('.appointment-card');
    const searchTerm = query.toLowerCase();
    
    appointmentCards.forEach(card => {
        const patientName = card.querySelector('.patient-name')?.textContent.toLowerCase() || '';
        const doctorName = card.querySelector('.doctor-name')?.textContent.toLowerCase() || '';
        const appointmentId = card.dataset.appointmentId || '';
        
        const shouldShow = patientName.includes(searchTerm) || 
                          doctorName.includes(searchTerm) || 
                          appointmentId.includes(searchTerm);
        
        card.style.display = shouldShow ? 'block' : 'none';
    });
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initAppointments();
});
