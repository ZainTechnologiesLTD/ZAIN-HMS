/* ZAIN HMS - IPD Module JavaScript */

// IPD Manager
function initIPD() {
    console.log('IPD module initialized');
    
    // Setup IPD functionality
    setupWardManagement();
    setupBedManagement();
    setupPatientMonitoring();
    setupRealTimeUpdates();
}

function setupWardManagement() {
    // Ward overview interactions
    const wardCards = document.querySelectorAll('.ward-card');
    wardCards.forEach(card => {
        card.addEventListener('click', function() {
            const wardId = this.dataset.wardId;
            if (wardId) {
                showWardDetails(wardId);
            }
        });
    });
}

function setupBedManagement() {
    // Bed interactions
    const bedItems = document.querySelectorAll('.bed-item');
    bedItems.forEach(bed => {
        bed.addEventListener('click', function() {
            const bedId = this.dataset.bedId;
            showBedDetails(bedId);
        });
        
        // Show tooltip on hover
        bed.addEventListener('mouseenter', function() {
            showBedTooltip(this);
        });
        
        bed.addEventListener('mouseleave', function() {
            hideBedTooltip(this);
        });
    });
}

function setupPatientMonitoring() {
    // Patient card interactions
    document.querySelectorAll('[data-action="view-patient"]').forEach(btn => {
        btn.addEventListener('click', function() {
            const patientId = this.dataset.patientId;
            viewPatientDetails(patientId);
        });
    });
    
    // Vital signs monitoring
    document.querySelectorAll('[data-action="update-vitals"]').forEach(btn => {
        btn.addEventListener('click', function() {
            const patientId = this.dataset.patientId;
            updateVitalSigns(patientId);
        });
    });
    
    // Discharge patient
    document.querySelectorAll('[data-action="discharge"]').forEach(btn => {
        btn.addEventListener('click', function() {
            const patientId = this.dataset.patientId;
            dischargePatient(patientId);
        });
    });
}

function setupRealTimeUpdates() {
    // Update bed status every 30 seconds
    setInterval(() => {
        updateBedStatuses();
        updatePatientVitals();
    }, 30000);
    
    // Check for critical patients every 5 minutes
    setInterval(() => {
        checkCriticalPatients();
    }, 300000);
}

// Ward Functions
function showWardDetails(wardId) {
    console.log('Showing ward details for:', wardId);
    
    // Create modal for ward details
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Ward Details</h5>
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
    
    // Load ward details
    fetch(`/ipd/wards/${wardId}/details/`)
        .then(response => response.json())
        .then(data => {
            const modalBody = modal.querySelector('.modal-body');
            modalBody.innerHTML = `
                <div class="row">
                    <div class="col-md-6">
                        <h6>Ward Information</h6>
                        <p><strong>Name:</strong> ${data.name}</p>
                        <p><strong>Type:</strong> ${data.ward_type}</p>
                        <p><strong>Capacity:</strong> ${data.total_beds} beds</p>
                        <p><strong>Occupancy:</strong> ${data.occupied_beds}/${data.total_beds} (${data.occupancy_rate}%)</p>
                    </div>
                    <div class="col-md-6">
                        <h6>Current Status</h6>
                        <p><strong>Available:</strong> ${data.available_beds}</p>
                        <p><strong>Occupied:</strong> ${data.occupied_beds}</p>
                        <p><strong>Reserved:</strong> ${data.reserved_beds}</p>
                        <p><strong>Maintenance:</strong> ${data.maintenance_beds}</p>
                    </div>
                </div>
                <div class="row mt-3">
                    <div class="col-12">
                        <h6>Bed Layout</h6>
                        <div class="bed-grid">
                            ${data.beds.map(bed => `
                                <div class="bed-card ${bed.status}" onclick="showBedDetails(${bed.id})">
                                    <div class="bed-number">${bed.number}</div>
                                    <div class="bed-status">${bed.status}</div>
                                    ${bed.patient ? `<div class="bed-patient">${bed.patient.name}</div>` : ''}
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            `;
        })
        .catch(error => {
            console.error('Error loading ward details:', error);
            modal.querySelector('.modal-body').innerHTML = '<p class="text-danger">Error loading ward details</p>';
        });
    
    // Clean up when modal is hidden
    modal.addEventListener('hidden.bs.modal', function() {
        document.body.removeChild(modal);
    });
}

// Bed Functions
function showBedDetails(bedId) {
    console.log('Showing bed details for:', bedId);
    
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Bed Details</h5>
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
                    <div id="bed-actions"></div>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    // Load bed details
    fetch(`/ipd/beds/${bedId}/details/`)
        .then(response => response.json())
        .then(data => {
            const modalBody = modal.querySelector('.modal-body');
            const actionsDiv = modal.querySelector('#bed-actions');
            
            modalBody.innerHTML = `
                <div class="bed-info">
                    <h6>Bed Information</h6>
                    <p><strong>Number:</strong> ${data.number}</p>
                    <p><strong>Ward:</strong> ${data.ward_name}</p>
                    <p><strong>Status:</strong> <span class="badge bg-${getStatusColor(data.status)}">${data.status}</span></p>
                    ${data.patient ? `
                        <h6 class="mt-3">Current Patient</h6>
                        <p><strong>Name:</strong> ${data.patient.name}</p>
                        <p><strong>ID:</strong> ${data.patient.id}</p>
                        <p><strong>Admission Date:</strong> ${data.patient.admission_date}</p>
                        <p><strong>Diagnosis:</strong> ${data.patient.diagnosis}</p>
                    ` : ''}
                </div>
            `;
            
            // Add action buttons based on bed status
            if (data.status === 'available') {
                actionsDiv.innerHTML = `
                    <button type="button" class="btn btn-primary" onclick="assignBed(${bedId})">Assign Patient</button>
                    <button type="button" class="btn btn-warning" onclick="setBedMaintenance(${bedId})">Set Maintenance</button>
                `;
            } else if (data.status === 'occupied') {
                actionsDiv.innerHTML = `
                    <button type="button" class="btn btn-info" onclick="viewPatientDetails(${data.patient.id})">View Patient</button>
                    <button type="button" class="btn btn-success" onclick="dischargePatient(${data.patient.id})">Discharge</button>
                `;
            } else if (data.status === 'maintenance') {
                actionsDiv.innerHTML = `
                    <button type="button" class="btn btn-success" onclick="setBedAvailable(${bedId})">Mark Available</button>
                `;
            }
        })
        .catch(error => {
            console.error('Error loading bed details:', error);
            modal.querySelector('.modal-body').innerHTML = '<p class="text-danger">Error loading bed details</p>';
        });
    
    // Clean up when modal is hidden
    modal.addEventListener('hidden.bs.modal', function() {
        document.body.removeChild(modal);
    });
}

function assignBed(bedId) {
    console.log('Assigning bed:', bedId);
    // Implementation for bed assignment
    showNotification('Bed assignment feature will be implemented', 'info');
}

function setBedMaintenance(bedId) {
    if (confirm('Set this bed to maintenance mode?')) {
        updateBedStatus(bedId, 'maintenance');
    }
}

function setBedAvailable(bedId) {
    if (confirm('Mark this bed as available?')) {
        updateBedStatus(bedId, 'available');
    }
}

function updateBedStatus(bedId, status) {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    
    fetch(`/ipd/beds/${bedId}/update-status/`, {
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
            showNotification('Bed status updated successfully', 'success');
            location.reload();
        } else {
            showNotification(data.message || 'Failed to update bed status', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred while updating bed status', 'error');
    });
}

// Patient Functions
function viewPatientDetails(patientId) {
    console.log('Viewing patient details for:', patientId);
    window.location.href = `/patients/${patientId}/`;
}

function updateVitalSigns(patientId) {
    console.log('Updating vital signs for patient:', patientId);
    
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Update Vital Signs</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <form id="vitals-form">
                        <input type="hidden" name="patient_id" value="${patientId}">
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Blood Pressure (Systolic)</label>
                                    <input type="number" class="form-control" name="bp_systolic" placeholder="120">
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Blood Pressure (Diastolic)</label>
                                    <input type="number" class="form-control" name="bp_diastolic" placeholder="80">
                                </div>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Heart Rate (BPM)</label>
                                    <input type="number" class="form-control" name="heart_rate" placeholder="72">
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Temperature (°F)</label>
                                    <input type="number" class="form-control" name="temperature" step="0.1" placeholder="98.6">
                                </div>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Respiratory Rate</label>
                                    <input type="number" class="form-control" name="respiratory_rate" placeholder="16">
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Oxygen Saturation (%)</label>
                                    <input type="number" class="form-control" name="oxygen_saturation" placeholder="98">
                                </div>
                            </div>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Notes</label>
                            <textarea class="form-control" name="notes" rows="3"></textarea>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-primary" onclick="submitVitalSigns()">Update Vitals</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    // Clean up when modal is hidden
    modal.addEventListener('hidden.bs.modal', function() {
        document.body.removeChild(modal);
    });
}

function submitVitalSigns() {
    const form = document.getElementById('vitals-form');
    const formData = new FormData(form);
    
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    if (csrfToken) {
        formData.append('csrfmiddlewaretoken', csrfToken);
    }
    
    fetch('/ipd/update-vitals/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Vital signs updated successfully', 'success');
            location.reload();
        } else {
            showNotification(data.message || 'Failed to update vital signs', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred while updating vital signs', 'error');
    });
}

function dischargePatient(patientId) {
    if (confirm('Are you sure you want to discharge this patient?')) {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        
        fetch(`/ipd/patients/${patientId}/discharge/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Patient discharged successfully', 'success');
                location.reload();
            } else {
                showNotification(data.message || 'Failed to discharge patient', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('An error occurred while discharging patient', 'error');
        });
    }
}

// Real-time Update Functions
function updateBedStatuses() {
    fetch('/ipd/api/bed-statuses/')
        .then(response => response.json())
        .then(data => {
            data.beds.forEach(bed => {
                updateBedDisplay(bed.id, bed.status, bed.patient);
            });
        })
        .catch(error => {
            console.error('Error updating bed statuses:', error);
        });
}

function updatePatientVitals() {
    const patientCards = document.querySelectorAll('[data-patient-id]');
    const patientIds = Array.from(patientCards).map(card => card.dataset.patientId);
    
    if (patientIds.length > 0) {
        fetch('/ipd/api/patient-vitals/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value
            },
            body: JSON.stringify({ patient_ids: patientIds })
        })
        .then(response => response.json())
        .then(data => {
            data.patients.forEach(patient => {
                updatePatientVitalsDisplay(patient.id, patient.vitals);
            });
        })
        .catch(error => {
            console.error('Error updating patient vitals:', error);
        });
    }
}

function checkCriticalPatients() {
    fetch('/ipd/api/critical-patients/')
        .then(response => response.json())
        .then(data => {
            if (data.critical_patients.length > 0) {
                data.critical_patients.forEach(patient => {
                    showCriticalAlert(patient);
                });
            }
        })
        .catch(error => {
            console.error('Error checking critical patients:', error);
        });
}

// Helper Functions
function updateBedDisplay(bedId, status, patient) {
    const bedElement = document.querySelector(`[data-bed-id="${bedId}"]`);
    if (bedElement) {
        bedElement.className = `bed-item bed-${status}`;
        
        if (patient) {
            const tooltip = bedElement.querySelector('.bed-tooltip');
            if (tooltip) {
                tooltip.innerHTML = `
                    ${patient.name}<br>
                    Admitted: ${patient.admission_date}
                `;
            }
        }
    }
}

function updatePatientVitalsDisplay(patientId, vitals) {
    const patientCard = document.querySelector(`[data-patient-id="${patientId}"]`);
    if (patientCard) {
        const vitalsContainer = patientCard.querySelector('.patient-vitals');
        if (vitalsContainer) {
            // Update vital signs display
            Object.keys(vitals).forEach(vitalType => {
                const vitalElement = vitalsContainer.querySelector(`[data-vital="${vitalType}"]`);
                if (vitalElement) {
                    const value = vitals[vitalType];
                    vitalElement.querySelector('.vital-value').textContent = value.value;
                    vitalElement.querySelector('.vital-value').className = `vital-value ${value.status}`;
                }
            });
        }
    }
}

function showCriticalAlert(patient) {
    showNotification(
        `Critical Alert: ${patient.name} in ${patient.ward} - ${patient.condition}`,
        'warning',
        0 // Don't auto-hide
    );
}

function showBedTooltip(bedElement) {
    const tooltip = bedElement.querySelector('.bed-tooltip');
    if (tooltip) {
        tooltip.style.display = 'block';
    }
}

function hideBedTooltip(bedElement) {
    const tooltip = bedElement.querySelector('.bed-tooltip');
    if (tooltip) {
        tooltip.style.display = 'none';
    }
}

function getStatusColor(status) {
    const colors = {
        'available': 'success',
        'occupied': 'danger',
        'reserved': 'warning',
        'maintenance': 'secondary'
    };
    return colors[status] || 'secondary';
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initIPD();
});
