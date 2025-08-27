/* ZAIN HMS - Patients Module JavaScript */

// Patients Manager
function initPatients() {
    console.log('Patients module initialized');
    
    // Setup patients functionality
    setupPatientActions();
    setupFilters();
    setupSearch();
    setupExportFunctions();
}

function setupPatientActions() {
    // View patient details
    document.querySelectorAll('[data-action="view-patient"]').forEach(btn => {
        btn.addEventListener('click', function() {
            const patientId = this.dataset.patientId;
            viewPatientDetails(patientId);
        });
    });
    
    // Edit patient
    document.querySelectorAll('[data-action="edit-patient"]').forEach(btn => {
        btn.addEventListener('click', function() {
            const patientId = this.dataset.patientId;
            editPatient(patientId);
        });
    });
    
    // Schedule appointment
    document.querySelectorAll('[data-action="schedule-appointment"]').forEach(btn => {
        btn.addEventListener('click', function() {
            const patientId = this.dataset.patientId;
            scheduleAppointment(patientId);
        });
    });
    
    // View medical history
    document.querySelectorAll('[data-action="view-history"]').forEach(btn => {
        btn.addEventListener('click', function() {
            const patientId = this.dataset.patientId;
            viewMedicalHistory(patientId);
        });
    });
}

function setupFilters() {
    const filterForm = document.querySelector('.patient-filters form');
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

function setupSearch() {
    const searchInput = document.querySelector('#patient-search');
    if (searchInput) {
        // Debounced search
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                searchPatients(this.value);
            }, 300);
        });
    }
}

function setupExportFunctions() {
    // Export functions
    document.querySelectorAll('[data-action="export"]').forEach(btn => {
        btn.addEventListener('click', function() {
            const format = this.dataset.format || 'excel';
            exportPatients(format);
        });
    });
}

// Patient Functions
function viewPatientDetails(patientId) {
    console.log('Viewing patient details:', patientId);
    
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Patient Details</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="text-center">
                        <div class="spinner-border" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    <div id="patient-actions"></div>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    // Load patient details
    fetch(`/patients/${patientId}/details/`)
        .then(response => response.json())
        .then(data => {
            const modalBody = modal.querySelector('.modal-body');
            const actionsDiv = modal.querySelector('#patient-actions');
            
            modalBody.innerHTML = `
                <div class="row">
                    <div class="col-md-6">
                        <h6>Personal Information</h6>
                        <p><strong>Name:</strong> ${data.full_name}</p>
                        <p><strong>Patient ID:</strong> ${data.patient_id}</p>
                        <p><strong>Date of Birth:</strong> ${data.date_of_birth}</p>
                        <p><strong>Age:</strong> ${data.age} years</p>
                        <p><strong>Gender:</strong> ${data.gender}</p>
                        <p><strong>Blood Group:</strong> ${data.blood_group}</p>
                        <p><strong>Phone:</strong> ${data.phone}</p>
                        <p><strong>Email:</strong> ${data.email}</p>
                    </div>
                    <div class="col-md-6">
                        <h6>Medical Information</h6>
                        <p><strong>Registration Date:</strong> ${data.created_at}</p>
                        <p><strong>Status:</strong> <span class="badge bg-${getPatientStatusColor(data.status)}">${data.status}</span></p>
                        <p><strong>Emergency Contact:</strong> ${data.emergency_contact_name}</p>
                        <p><strong>Emergency Phone:</strong> ${data.emergency_contact_phone}</p>
                        ${data.insurance_number ? `<p><strong>Insurance:</strong> ${data.insurance_number}</p>` : ''}
                        ${data.allergies ? `<p><strong>Allergies:</strong> ${data.allergies}</p>` : ''}
                        ${data.medical_conditions ? `<p><strong>Medical Conditions:</strong> ${data.medical_conditions}</p>` : ''}
                    </div>
                </div>
                ${data.address ? `
                    <div class="row mt-3">
                        <div class="col-12">
                            <h6>Address</h6>
                            <p>${data.address}</p>
                        </div>
                    </div>
                ` : ''}
                <div class="row mt-3">
                    <div class="col-12">
                        <h6>Recent Appointments</h6>
                        <div class="table-responsive">
                            <table class="table table-sm">
                                <thead>
                                    <tr>
                                        <th>Date</th>
                                        <th>Doctor</th>
                                        <th>Department</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${data.recent_appointments.map(apt => `
                                        <tr>
                                            <td>${apt.appointment_date}</td>
                                            <td>Dr. ${apt.doctor_name}</td>
                                            <td>${apt.department}</td>
                                            <td><span class="badge bg-${getStatusColor(apt.status)}">${apt.status}</span></td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            `;
            
            // Add action buttons
            actionsDiv.innerHTML = `
                <button type="button" class="btn btn-primary" onclick="editPatient(${patientId})">Edit Patient</button>
                <button type="button" class="btn btn-success" onclick="scheduleAppointment(${patientId})">Schedule Appointment</button>
                <button type="button" class="btn btn-info" onclick="viewMedicalHistory(${patientId})">Medical History</button>
            `;
        })
        .catch(error => {
            console.error('Error loading patient details:', error);
            modal.querySelector('.modal-body').innerHTML = '<p class="text-danger">Error loading patient details</p>';
        });
    
    // Clean up when modal is hidden
    modal.addEventListener('hidden.bs.modal', function() {
        document.body.removeChild(modal);
    });
}

function editPatient(patientId) {
    console.log('Editing patient:', patientId);
    window.location.href = `/patients/${patientId}/edit/`;
}

function scheduleAppointment(patientId) {
    console.log('Scheduling appointment for patient:', patientId);
    
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Schedule Appointment</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <form id="appointment-form">
                        <input type="hidden" name="patient_id" value="${patientId}">
                        
                        <div class="mb-3">
                            <label class="form-label">Doctor</label>
                            <select class="form-select" name="doctor_id" required>
                                <option value="">Select doctor...</option>
                                <!-- Doctors will be loaded dynamically -->
                            </select>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Date</label>
                            <input type="date" class="form-control" name="appointment_date" required>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Time</label>
                            <select class="form-select" name="appointment_time" required>
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
                            <textarea class="form-control" name="reason" rows="3" placeholder="Brief description..."></textarea>
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
                    <button type="button" class="btn btn-primary" onclick="submitAppointment()">Schedule</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    // Set minimum date to today
    const dateInput = modal.querySelector('[name="appointment_date"]');
    const today = new Date().toISOString().split('T')[0];
    dateInput.min = today;
    
    // Load doctors
    loadDoctorsForAppointment(modal);
    
    // Clean up when modal is hidden
    modal.addEventListener('hidden.bs.modal', function() {
        document.body.removeChild(modal);
    });
}

function loadDoctorsForAppointment(modal) {
    const doctorSelect = modal.querySelector('[name="doctor_id"]');
    
    fetch('/api/doctors/')
        .then(response => response.json())
        .then(data => {
            data.doctors.forEach(doctor => {
                const option = document.createElement('option');
                option.value = doctor.id;
                option.textContent = `Dr. ${doctor.name} - ${doctor.department}`;
                doctorSelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error loading doctors:', error);
        });
}

function submitAppointment() {
    const form = document.getElementById('appointment-form');
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
            showNotification('Appointment scheduled successfully', 'success');
            // Close modal and optionally refresh
            const modal = bootstrap.Modal.getInstance(document.querySelector('.modal'));
            modal.hide();
        } else {
            showNotification(data.message || 'Failed to schedule appointment', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred while scheduling appointment', 'error');
    });
}

function viewMedicalHistory(patientId) {
    console.log('Viewing medical history for patient:', patientId);
    window.location.href = `/patients/${patientId}/medical-history/`;
}

// Search and Filter Functions
function searchPatients(query) {
    const patientCards = document.querySelectorAll('.patient-card');
    const searchTerm = query.toLowerCase();
    
    patientCards.forEach(card => {
        const patientName = card.querySelector('.patient-name')?.textContent.toLowerCase() || '';
        const patientId = card.querySelector('.patient-id')?.textContent.toLowerCase() || '';
        const phone = card.querySelector('.patient-phone')?.textContent.toLowerCase() || '';
        
        const shouldShow = patientName.includes(searchTerm) || 
                          patientId.includes(searchTerm) || 
                          phone.includes(searchTerm);
        
        card.style.display = shouldShow ? 'block' : 'none';
    });
    
    // Update results count
    const visibleCards = document.querySelectorAll('.patient-card[style*="block"], .patient-card:not([style*="none"])');
    const resultsCount = visibleCards.length;
    
    // Show results count if search is active
    if (query.trim()) {
        let resultsDiv = document.getElementById('search-results');
        if (!resultsDiv) {
            resultsDiv = document.createElement('div');
            resultsDiv.id = 'search-results';
            resultsDiv.className = 'alert alert-info mb-3';
            document.querySelector('.patients-grid').parentNode.insertBefore(resultsDiv, document.querySelector('.patients-grid'));
        }
        resultsDiv.textContent = `Found ${resultsCount} patient(s) matching "${query}"`;
    } else {
        const resultsDiv = document.getElementById('search-results');
        if (resultsDiv) {
            resultsDiv.remove();
        }
    }
}

// Export Functions
function exportPatients(format) {
    const searchParams = new URLSearchParams(window.location.search);
    searchParams.set('export', format);
    
    const exportUrl = '/patients/export/?' + searchParams.toString();
    window.open(exportUrl, '_blank');
}

// Patient Statistics Functions
function updatePatientStats() {
    fetch('/patients/api/stats/')
        .then(response => response.json())
        .then(data => {
            updateStatCard('total-patients', data.total_patients);
            updateStatCard('new-patients-today', data.new_patients_today);
            updateStatCard('active-patients', data.active_patients);
            updateStatCard('appointments-today', data.appointments_today);
        })
        .catch(error => {
            console.error('Error updating patient stats:', error);
        });
}

function updateStatCard(cardId, value) {
    const card = document.getElementById(cardId);
    if (card) {
        const numberElement = card.querySelector('.stat-number');
        if (numberElement) {
            // Animate the number change
            animateNumber(numberElement, value);
        }
    }
}

function animateNumber(element, targetValue) {
    const currentValue = parseInt(element.textContent) || 0;
    const increment = targetValue > currentValue ? 1 : -1;
    const timer = setInterval(() => {
        const current = parseInt(element.textContent) || 0;
        if (current === targetValue) {
            clearInterval(timer);
        } else {
            element.textContent = current + increment;
        }
    }, 50);
}

// Bulk Operations
function selectAllPatients() {
    const checkboxes = document.querySelectorAll('.patient-checkbox');
    const selectAllCheckbox = document.getElementById('select-all-patients');
    
    checkboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
    });
    
    updateBulkActions();
}

function updateBulkActions() {
    const checkedBoxes = document.querySelectorAll('.patient-checkbox:checked');
    const bulkActions = document.getElementById('bulk-actions');
    
    if (checkedBoxes.length > 0) {
        if (bulkActions) {
            bulkActions.style.display = 'block';
            bulkActions.querySelector('.selected-count').textContent = checkedBoxes.length;
        }
    } else {
        if (bulkActions) {
            bulkActions.style.display = 'none';
        }
    }
}

function bulkExport() {
    const checkedBoxes = document.querySelectorAll('.patient-checkbox:checked');
    const patientIds = Array.from(checkedBoxes).map(cb => cb.value);
    
    if (patientIds.length === 0) {
        showNotification('Please select patients to export', 'warning');
        return;
    }
    
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/patients/bulk-export/';
    
    const csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = 'csrfmiddlewaretoken';
    csrfInput.value = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    form.appendChild(csrfInput);
    
    patientIds.forEach(id => {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'patient_ids';
        input.value = id;
        form.appendChild(input);
    });
    
    document.body.appendChild(form);
    form.submit();
    document.body.removeChild(form);
}

// Helper Functions
function getPatientStatusColor(status) {
    const colors = {
        'ACTIVE': 'success',
        'INACTIVE': 'secondary',
        'DISCHARGED': 'info',
        'DECEASED': 'dark'
    };
    return colors[status] || 'secondary';
}

function getStatusColor(status) {
    const colors = {
        'SCHEDULED': 'primary',
        'COMPLETED': 'success',
        'CANCELLED': 'danger',
        'PENDING': 'warning'
    };
    return colors[status] || 'secondary';
}

// Age calculation helper
function calculateAge(birthDate) {
    const today = new Date();
    const birth = new Date(birthDate);
    let age = today.getFullYear() - birth.getFullYear();
    const monthDiff = today.getMonth() - birth.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
        age--;
    }
    
    return age;
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initPatients();
    
    // Setup bulk selection
    const selectAllCheckbox = document.getElementById('select-all-patients');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', selectAllPatients);
    }
    
    // Setup individual checkboxes
    document.querySelectorAll('.patient-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', updateBulkActions);
    });
    
    // Update stats periodically
    setInterval(updatePatientStats, 60000); // Every minute
});
