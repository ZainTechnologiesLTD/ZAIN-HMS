/**
 * Enhanced Appointment UI JavaScript
 * Handles interactions for the enhanced appointment management interface
 */

document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize components when DOM is ready
    initializeAppointmentUI();
    
});

function initializeAppointmentUI() {
    // Initialize date pickers
    initializeDatePickers();
    
    // Initialize search functionality
    initializeSearch();
    
    // Initialize calendar if present
    initializeCalendar();
    
    // Initialize form wizard
    initializeWizard();
    
    // Initialize auto-refresh
    initializeAutoRefresh();
    
    // Initialize tooltips and popovers
    initializeBootstrapComponents();
}

/**
 * Initialize date picker components
 */
function initializeDatePickers() {
    if (typeof flatpickr !== 'undefined') {
        // Date picker for appointment date
        flatpickr('.appointment-date-picker', {
            dateFormat: 'Y-m-d',
            minDate: 'today',
            disable: [
                function(date) {
                    // Disable Sundays (0 = Sunday)
                    return date.getDay() === 0;
                }
            ]
        });
        
        // Time picker for appointment time
        flatpickr('.appointment-time-picker', {
            enableTime: true,
            noCalendar: true,
            dateFormat: 'H:i',
            time_24hr: true,
            minuteIncrement: 30
        });
        
        // Date range picker for filters
        flatpickr('.date-range-picker', {
            mode: 'range',
            dateFormat: 'Y-m-d'
        });
    }
}

/**
 * Initialize search functionality
 */
function initializeSearch() {
    const searchInput = document.getElementById('appointmentSearch');
    if (searchInput) {
        let searchTimeout;
        
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                performSearch(this.value);
            }, 300);
        });
    }
    
    // Initialize filter dropdowns
    const filterSelects = document.querySelectorAll('.appointment-filter');
    filterSelects.forEach(select => {
        select.addEventListener('change', function() {
            applyFilters();
        });
    });
}

/**
 * Perform search with debouncing
 */
function performSearch(query) {
    const url = new URL(window.location);
    url.searchParams.set('search', query);
    url.searchParams.set('page', '1'); // Reset to first page
    
    // Use HTMX if available, otherwise reload page
    if (typeof htmx !== 'undefined') {
        htmx.ajax('GET', url.toString(), {
            target: '#appointment-list-container',
            swap: 'innerHTML'
        });
    } else {
        window.location.href = url.toString();
    }
}

/**
 * Apply all active filters
 */
function applyFilters() {
    const url = new URL(window.location);
    
    // Collect all filter values
    const filters = {
        search: document.getElementById('appointmentSearch')?.value || '',
        status: document.getElementById('statusFilter')?.value || '',
        priority: document.getElementById('priorityFilter')?.value || '',
        doctor: document.getElementById('doctorFilter')?.value || '',
        date_from: document.getElementById('dateFromFilter')?.value || '',
        date_to: document.getElementById('dateToFilter')?.value || ''
    };
    
    // Update URL parameters
    Object.keys(filters).forEach(key => {
        if (filters[key]) {
            url.searchParams.set(key, filters[key]);
        } else {
            url.searchParams.delete(key);
        }
    });
    
    url.searchParams.set('page', '1'); // Reset pagination
    
    // Apply filters
    if (typeof htmx !== 'undefined') {
        htmx.ajax('GET', url.toString(), {
            target: '#appointment-list-container',
            swap: 'innerHTML'
        });
    } else {
        window.location.href = url.toString();
    }
}

/**
 * Initialize FullCalendar
 */
function initializeCalendar() {
    const calendarEl = document.getElementById('appointmentCalendar');
    if (calendarEl && typeof FullCalendar !== 'undefined') {
        const calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay'
            },
            events: {
                url: calendarEl.dataset.eventsUrl || '/appointments/calendar/events/',
                method: 'GET',
                failure: function() {
                    alert('There was an error while fetching events!');
                }
            },
            eventClick: function(info) {
                showAppointmentModal(info.event.id);
            },
            eventMouseEnter: function(info) {
                const props = info.event.extendedProps;
                const tooltip = `
                    <div class="calendar-tooltip">
                        <strong>${props.patient}</strong><br>
                        Doctor: ${props.doctor}<br>
                        Status: ${props.status}<br>
                        ${props.chief_complaint ? `Complaint: ${props.chief_complaint}` : ''}
                    </div>
                `;
                
                // Show tooltip (you might want to use a tooltip library)
                info.el.setAttribute('title', tooltip);
            },
            height: 'auto',
            aspectRatio: 1.8,
            dayMaxEvents: 3,
            moreLinkClick: 'popover'
        });
        
        calendar.render();
        
        // Store calendar instance globally for external access
        window.appointmentCalendar = calendar;
        
        // Doctor filter for calendar
        const doctorFilterSelect = document.getElementById('calendarDoctorFilter');
        if (doctorFilterSelect) {
            doctorFilterSelect.addEventListener('change', function() {
                const doctorId = this.value;
                calendar.removeAllEventSources();
                calendar.addEventSource({
                    url: calendarEl.dataset.eventsUrl || '/appointments/calendar/events/',
                    extraParams: {
                        doctor: doctorId
                    }
                });
            });
        }
    }
}

/**
 * Initialize appointment creation wizard
 */
function initializeWizard() {
    const wizardContainer = document.getElementById('appointmentWizard');
    if (!wizardContainer) return;
    
    const steps = wizardContainer.querySelectorAll('.wizard-step');
    const nextBtns = wizardContainer.querySelectorAll('.btn-next');
    const prevBtns = wizardContainer.querySelectorAll('.btn-prev');
    const progressBar = wizardContainer.querySelector('.wizard-progress');
    
    let currentStep = 0;
    
    function showStep(stepIndex) {
        // Hide all steps
        steps.forEach((step, index) => {
            step.classList.toggle('active', index === stepIndex);
        });
        
        // Update progress bar
        if (progressBar) {
            const progress = ((stepIndex + 1) / steps.length) * 100;
            progressBar.style.width = progress + '%';
            progressBar.setAttribute('aria-valuenow', progress);
        }
        
        // Update step indicator
        const indicators = wizardContainer.querySelectorAll('.step-indicator');
        indicators.forEach((indicator, index) => {
            indicator.classList.toggle('active', index === stepIndex);
            indicator.classList.toggle('completed', index < stepIndex);
        });
        
        currentStep = stepIndex;
    }
    
    // Next button handlers
    nextBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            if (validateCurrentStep()) {
                if (currentStep < steps.length - 1) {
                    showStep(currentStep + 1);
                }
            }
        });
    });
    
    // Previous button handlers
    prevBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            if (currentStep > 0) {
                showStep(currentStep - 1);
            }
        });
    });
    
    // Patient search in wizard
    const patientSearch = document.getElementById('patientSearch');
    if (patientSearch) {
        patientSearch.addEventListener('input', function() {
            searchPatients(this.value);
        });
    }
    
    // Doctor specialty filter
    const specialtyFilter = document.getElementById('specialtyFilter');
    if (specialtyFilter) {
        specialtyFilter.addEventListener('change', function() {
            filterDoctorsBySpecialty(this.value);
        });
    }
    
    // Date selection handler
    const dateInput = document.getElementById('appointmentDate');
    if (dateInput) {
        dateInput.addEventListener('change', function() {
            loadAvailableTimeSlots(this.value);
        });
    }
    
    // Initialize first step
    showStep(0);
}

/**
 * Validate current wizard step
 */
function validateCurrentStep() {
    const currentStepEl = document.querySelector('.wizard-step.active');
    if (!currentStepEl) return true;
    
    const requiredFields = currentStepEl.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

/**
 * Search patients for wizard
 */
function searchPatients(query) {
    if (query.length < 2) return;
    
    fetch(`/appointments/search-patients/?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            const resultsContainer = document.getElementById('patientSearchResults');
            if (resultsContainer) {
                resultsContainer.innerHTML = '';
                
                data.results.forEach(patient => {
                    const patientCard = document.createElement('div');
                    patientCard.className = 'patient-search-result';
                    patientCard.innerHTML = `
                        <div class="d-flex justify-content-between align-items-center p-3 border rounded mb-2 cursor-pointer">
                            <div>
                                <strong>${patient.text}</strong>
                                <br>
                                <small class="text-muted">${patient.phone}</small>
                            </div>
                            <button type="button" class="btn btn-sm btn-primary select-patient" data-patient-id="${patient.id}">
                                Select
                            </button>
                        </div>
                    `;
                    
                    resultsContainer.appendChild(patientCard);
                });
                
                // Add click handlers for selection
                resultsContainer.querySelectorAll('.select-patient').forEach(btn => {
                    btn.addEventListener('click', function() {
                        selectPatient(this.dataset.patientId);
                    });
                });
            }
        })
        .catch(error => {
            console.error('Error searching patients:', error);
        });
}

/**
 * Select patient in wizard
 */
function selectPatient(patientId) {
    const hiddenInput = document.getElementById('selectedPatient');
    if (hiddenInput) {
        hiddenInput.value = patientId;
    }
    
    // Update UI to show selected patient
    const selectedContainer = document.getElementById('selectedPatientInfo');
    if (selectedContainer) {
        selectedContainer.innerHTML = '<div class="alert alert-success">Patient selected!</div>';
    }
    
    // Clear search results
    const resultsContainer = document.getElementById('patientSearchResults');
    if (resultsContainer) {
        resultsContainer.innerHTML = '';
    }
}

/**
 * Load available time slots for selected date and doctor
 */
function loadAvailableTimeSlots(date) {
    const doctorId = document.getElementById('selectedDoctor')?.value;
    if (!doctorId || !date) return;
    
    fetch(`/appointments/get-available-time-slots/?doctor_id=${doctorId}&date=${date}`)
        .then(response => response.json())
        .then(data => {
            const slotsContainer = document.getElementById('timeSlots');
            if (slotsContainer) {
                slotsContainer.innerHTML = '';
                
                if (data.slots.length === 0) {
                    slotsContainer.innerHTML = '<div class="alert alert-warning">No available time slots for this date.</div>';
                    return;
                }
                
                data.slots.forEach(slot => {
                    const slotBtn = document.createElement('button');
                    slotBtn.type = 'button';
                    slotBtn.className = `btn btn-outline-primary time-slot ${slot.available ? '' : 'disabled'}`;
                    slotBtn.textContent = slot.display;
                    slotBtn.dataset.time = slot.time;
                    
                    if (slot.available) {
                        slotBtn.addEventListener('click', function() {
                            selectTimeSlot(this);
                        });
                    }
                    
                    slotsContainer.appendChild(slotBtn);
                });
            }
        })
        .catch(error => {
            console.error('Error loading time slots:', error);
        });
}

/**
 * Select time slot
 */
function selectTimeSlot(button) {
    // Remove active class from all time slots
    document.querySelectorAll('.time-slot').forEach(btn => {
        btn.classList.remove('active');
        btn.classList.add('btn-outline-primary');
        btn.classList.remove('btn-primary');
    });
    
    // Add active class to selected slot
    button.classList.add('active');
    button.classList.remove('btn-outline-primary');
    button.classList.add('btn-primary');
    
    // Update hidden input
    const timeInput = document.getElementById('selectedTime');
    if (timeInput) {
        timeInput.value = button.dataset.time;
    }
}

/**
 * Initialize auto-refresh for widgets
 */
function initializeAutoRefresh() {
    const autoRefreshElements = document.querySelectorAll('[data-auto-refresh]');
    
    autoRefreshElements.forEach(element => {
        const interval = parseInt(element.dataset.autoRefresh) || 30000; // Default 30 seconds
        const url = element.dataset.refreshUrl;
        
        if (url) {
            setInterval(() => {
                if (typeof htmx !== 'undefined') {
                    htmx.ajax('GET', url, {
                        target: element,
                        swap: 'innerHTML'
                    });
                }
            }, interval);
        }
    });
}

/**
 * Initialize Bootstrap components
 */
function initializeBootstrapComponents() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Initialize modals
    const modalTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="modal"]'));
    modalTriggerList.forEach(modalTriggerEl => {
        modalTriggerEl.addEventListener('click', function() {
            const targetModal = document.querySelector(this.dataset.bsTarget);
            if (targetModal) {
                const modal = new bootstrap.Modal(targetModal);
                modal.show();
            }
        });
    });
}

/**
 * Show appointment details in modal
 */
function showAppointmentModal(appointmentId) {
    const modalUrl = `/appointments/${appointmentId}/modal/`;
    
    fetch(modalUrl)
        .then(response => response.text())
        .then(html => {
            // Create or update modal content
            let modal = document.getElementById('appointmentDetailModal');
            if (!modal) {
                modal = document.createElement('div');
                modal.id = 'appointmentDetailModal';
                document.body.appendChild(modal);
            }
            
            modal.innerHTML = html;
            
            // Show modal
            const bsModal = new bootstrap.Modal(modal.querySelector('.modal'));
            bsModal.show();
        })
        .catch(error => {
            console.error('Error loading appointment details:', error);
        });
}

/**
 * Handle appointment status changes
 */
function updateAppointmentStatus(appointmentId, newStatus) {
    const formData = new FormData();
    formData.append('status', newStatus);
    formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
    
    fetch(`/appointments/${appointmentId}/`, {
        method: 'PATCH',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update UI to reflect status change
            location.reload(); // Simple approach, could be more sophisticated
        } else {
            alert('Error updating appointment status');
        }
    })
    .catch(error => {
        console.error('Error updating status:', error);
    });
}

/**
 * Export appointments
 */
function exportAppointments(format = 'csv') {
    const url = new URL('/appointments/export/', window.location.origin);
    
    // Add current filters to export
    const filters = {
        search: document.getElementById('appointmentSearch')?.value || '',
        status: document.getElementById('statusFilter')?.value || '',
        date_from: document.getElementById('dateFromFilter')?.value || '',
        date_to: document.getElementById('dateToFilter')?.value || ''
    };
    
    Object.keys(filters).forEach(key => {
        if (filters[key]) {
            url.searchParams.set(key, filters[key]);
        }
    });
    
    url.searchParams.set('format', format);
    
    // Download file
    window.open(url.toString(), '_blank');
}

/**
 * Utility function to show toast notifications
 */
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
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
    
    // Remove toast element after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

/**
 * Create toast container if it doesn't exist
 */
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '1050';
    document.body.appendChild(container);
    return container;
}

// Global functions for external access
window.AppointmentUI = {
    showToast,
    updateAppointmentStatus,
    exportAppointments,
    showAppointmentModal,
    performSearch,
    applyFilters
};
