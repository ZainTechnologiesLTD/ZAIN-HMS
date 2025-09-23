// Global selection functions - accessible to inline onclick handlers
window.selectPatient = function(el, id, name, phone) {
    console.log('selectPatient called with:', { el, id, name, phone });

    // Update selectedData
    if (window.selectedData) {
        window.selectedData.patient = { id, name, phone };
    }

    // Update hidden field
    const hiddenField = document.getElementById('selectedPatientId');
    if (hiddenField) {
        hiddenField.value = id;
        console.log('Set hidden field value to:', id);
    }

    // Update UI - remove selected class from all cards
    document.querySelectorAll('.patient-card').forEach(card => {
        card.classList.remove('selected');
    });

    // Add selected class to clicked card
    if (el) {
        el.classList.add('selected');
    }

    // Show success message
    alert('Selected patient: ' + name);

    console.log('Patient selection completed');
}

window.selectDoctor = function(el, id, name, specialty) {
    console.log('selectDoctor called with:', { el, id, name, specialty });

    // Update selectedData
    if (window.selectedData) {
        window.selectedData.doctor = { id, name, specialty };
    }

    // Update hidden field
    const hiddenField = document.getElementById('selectedDoctorId');
    if (hiddenField) {
        hiddenField.value = id;
        console.log('Set doctor hidden field value to:', id);
    }

    // Update UI - remove selected class from all cards
    document.querySelectorAll('.doctor-card').forEach(card => {
        card.classList.remove('selected');
    });

    // Add selected class to clicked card
    if (el) {
        el.classList.add('selected');
    }

    // Show success message
    alert('Selected doctor: ' + name);

    // Load time slots if date is selected
    if (window.selectedData && window.selectedData.date) {
        window.loadTimeSlots();
    }

    console.log('Doctor selection completed');
}

window.selectTimeSlot = function(el, time) {
    console.log('selectTimeSlot called with:', { el, time });

    // Update selectedData
    if (window.selectedData) {
        window.selectedData.time = time;
        document.getElementById('selectedDateTime').value = `${window.selectedData.date} ${time}`;
        console.log('Set time slot to:', time);
    }

    // Update UI - remove selected class from all slots
    document.querySelectorAll('.time-slot').forEach(slot => {
        slot.classList.remove('selected');
    });

    // Add selected class to clicked slot
    if (el) {
        el.classList.add('selected');
    }

    // Show success message
    alert('Selected time: ' + time);

    console.log('Time slot selection completed');
}

document.addEventListener('DOMContentLoaded', function() {
    let currentStep = 1;
    const totalSteps = 5;
    let selectedData = {
        patient: null,
        doctor: null,
        date: null,
        time: null,
        type: null
    };

    // Make selectedData globally accessible
    window.selectedData = selectedData;

    // Initialize date picker
    const datePicker = flatpickr("#appointmentDate", {
        minDate: "today",
        dateFormat: "Y-m-d",
        onChange: function(selectedDates, dateStr, instance) {
            selectedData.date = dateStr;
            loadTimeSlots();
        }
    });

    // Patient search functionality
    let searchTimeout;
    document.getElementById('patientSearch').addEventListener('input', function(e) {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            searchPatients(e.target.value);
        }, 300);
    });

    // Specialty badge selection
    document.querySelectorAll('.specialty-badge').forEach(badge => {
        badge.addEventListener('click', function() {
            document.querySelectorAll('.specialty-badge').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            loadDoctorsBySpecialty(this.dataset.specialty);
        });
    });

    // Navigation buttons
    document.getElementById('nextBtn').addEventListener('click', nextStep);
    document.getElementById('prevBtn').addEventListener('click', prevStep);
    document.getElementById('submitBtn').addEventListener('click', submitForm);

    // Form validation before proceeding
    function validateStep(step) {
        switch(step) {
            case 1:
                return selectedData.patient !== null;
            case 2:
                return selectedData.doctor !== null;
            case 3:
                return selectedData.date !== null && selectedData.time !== null;
            case 4:
                const complaint = document.getElementById('chiefComplaint').value.trim();
                return complaint.length > 0;
            default:
                return true;
        }
    }

    function nextStep() {
        if (!validateStep(currentStep)) {
            showAlert('Please complete all required fields before proceeding.', 'warning');
            return;
        }

        if (currentStep < totalSteps) {
            currentStep++;
            updateWizard();
        }
    }

    function prevStep() {
        if (currentStep > 1) {
            currentStep--;
            updateWizard();
        }
    }

    function updateWizard() {
        // Hide all steps
        document.querySelectorAll('.wizard-step').forEach(step => {
            step.classList.remove('active');
        });

        // Show current step
        document.getElementById(`step${currentStep}`).classList.add('active');

        // Update step indicators
        document.querySelectorAll('.step').forEach((step, index) => {
            const stepNum = index + 1;
            step.classList.remove('active', 'completed');

            if (stepNum < currentStep) {
                step.classList.add('completed');
            } else if (stepNum === currentStep) {
                step.classList.add('active');
            }
        });

        // Update navigation buttons
        document.getElementById('prevBtn').style.display = currentStep > 1 ? 'block' : 'none';
        document.getElementById('nextBtn').style.display = currentStep < totalSteps ? 'block' : 'none';
        document.getElementById('submitBtn').style.display = currentStep === totalSteps ? 'block' : 'none';

        // Update summary on last step
        if (currentStep === totalSteps) {
            updateSummary();
        }
    }

    function searchPatients(query) {
        if (query.length < 2) {
            document.getElementById('patientResults').innerHTML = '';
            return;
        }

        showLoading(true);

        fetch(`{% url 'appointments:search_patients' %}?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                displayPatients(data.results);
                showLoading(false);
            })
            .catch(error => {
                console.error('Error:', error);
                showLoading(false);
            });
    }

    function displayPatients(patients) {
        const container = document.getElementById('patientResults');

        if (patients.length === 0) {
            container.innerHTML = `
                <div class="col-12 text-center">
                    <div class="patient-card">
                        <i class="bi bi-person-x fs-1 text-muted mb-3"></i>
                        <h5 class="text-muted">No patients found</h5>
                        <p class="text-muted mb-0">Try a different search term or add a new patient</p>
                    </div>
                </div>
            `;
            return;
        }

        console.log('Displaying patients:', patients);

        container.innerHTML = patients.map(patient => {
            const patientId = patient.id;
            const patientName = patient.text;
            const patientPhone = patient.phone;

            return `
            <div class="col-md-6 col-lg-4">
                <div class="patient-card" onclick="window.selectPatient(this, '${patientId}', '${patientName.replace(/'/g, "\\'")}', '${patientPhone}')">
                    <div class="d-flex align-items-center">
                        <div class="me-3">
                            <div class="bg-primary rounded-circle d-flex align-items-center justify-content-center" style="width: 50px; height: 50px;">
                                <i class="bi bi-person text-white fs-4"></i>
                            </div>
                        </div>
                        <div>
                            <h6 class="mb-1">${patientName}</h6>
                            <small class="text-muted">${patientPhone}</small>
                        </div>
                    </div>
                    <div class="text-end mt-2">
                        <small class="text-primary">Click to select</small>
                    </div>
                </div>
            </div>
            `;
        }).join('');

        console.log('Patient cards rendered, checking if selectPatient function exists:', typeof window.selectPatient);
    }

    function loadDoctorsBySpecialty(specialty) {
        showLoading(true);

        fetch(`{% url 'appointments:get_doctors' %}?specialty=${specialty}`)
            .then(response => response.json())
            .then(data => {
                displayDoctors(data.results);
                showLoading(false);
            })
            .catch(error => {
                console.error('Error:', error);
                showLoading(false);
            });
    }

    function displayDoctors(doctors) {
        const container = document.getElementById('doctorResults');

        if (doctors.length === 0) {
            container.innerHTML = `
                <div class="text-center">
                    <i class="bi bi-person-badge fs-1 text-muted mb-3"></i>
                    <h5 class="text-muted">No doctors available</h5>
                    <p class="text-muted mb-0">Please select a different specialty</p>
                </div>
            `;
            return;
        }

        container.innerHTML = doctors.map(doctor => {
            const doctorId = doctor.id;
            const doctorName = doctor.name;
            const doctorSpecialty = doctor.specialty;

            return `
            <div class="doctor-card" onclick="window.selectDoctor(this, '${doctorId}', '${doctorName.replace(/'/g, "\\'")}', '${doctorSpecialty}')">
                <div class="doctor-avatar">
                    ${doctorName.split(' ').map(n => n[0]).join('').substring(0, 2)}
                </div>
                <h6 class="mb-1">${doctorName}</h6>
                <small class="text-muted">${doctorSpecialty}</small>
                <div class="mt-3">
                    <small class="text-primary">Click to select</small>
                </div>
            </div>
            `;
        }).join('');
    }    function loadTimeSlots() {
        console.log('loadTimeSlots called');
        console.log('selectedData:', window.selectedData);

        if (!selectedData.doctor || !selectedData.date) {
            console.log('Missing doctor or date, returning early');
            return;
        }

        console.log('Loading time slots for doctor:', selectedData.doctor.id, 'on date:', selectedData.date);
        showLoading(true);

        const url = `{% url 'appointments:get_available_time_slots' %}?doctor_id=${selectedData.doctor.id}&date=${selectedData.date}`;
        console.log('Fetching URL:', url);

        fetch(url)
            .then(response => {
                console.log('Response status:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('Received time slots data:', data);
                displayTimeSlots(data.slots);
                showLoading(false);
            })
            .catch(error => {
                console.error('Error loading time slots:', error);
                showLoading(false);
            });
    }

    function displayTimeSlots(slots) {
        const container = document.getElementById('timeSlots');

        console.log('displayTimeSlots called with slots:', slots);

        if (slots.length === 0) {
            container.innerHTML = `
                <div class="text-center">
                    <i class="bi bi-clock fs-1 text-muted mb-3"></i>
                    <h5 class="text-muted">No available slots</h5>
                    <p class="text-muted mb-0">Please select a different date</p>
                </div>
            `;
            return;
        }

        container.innerHTML = slots.map(slot => {
            const slotTime = slot.time;
            const isAvailable = slot.available;
            console.log('Processing slot:', { time: slotTime, available: isAvailable });

            if (isAvailable) {
                return `
                <div class="time-slot"
                     onclick="console.log('Time slot clicked:', '${slotTime}'); window.selectTimeSlot(this, '${slotTime}')">
                    ${slotTime}
                </div>
                `;
            } else {
                return `
                <div class="time-slot unavailable" title="Already booked">
                    ${slotTime}
                </div>
                `;
            }
        }).join('');

        console.log('Time slots rendered, checking if selectTimeSlot function exists:', typeof window.selectTimeSlot);
    }

    function updateSummary() {
        document.getElementById('summaryPatient').textContent = selectedData.patient ? selectedData.patient.name : '-';
        document.getElementById('summaryDoctor').textContent = selectedData.doctor ? `Dr. ${selectedData.doctor.name}` : '-';
        document.getElementById('summaryDate').textContent = selectedData.date || '-';
        document.getElementById('summaryTime').textContent = selectedData.time || '-';
        document.getElementById('summaryType').textContent = document.getElementById('appointmentType').value || '-';
        document.getElementById('summaryComplaint').textContent = document.getElementById('chiefComplaint').value || '-';
        document.getElementById('summaryPriority').textContent = document.getElementById('priority').value || '-';
        document.getElementById('summaryFee').textContent = document.getElementById('consultationFee').value ? `$${document.getElementById('consultationFee').value}` : '-';
    }

    function submitForm() {
        if (!validateStep(4)) {
            showAlert('Please complete all required fields.', 'error');
            return;
        }

        showLoading(true);

        const formData = new FormData(document.getElementById('appointmentWizardForm'));

        fetch('{% url "appointments:appointment_create" %}', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            showLoading(false);
            if (data.success) {
                showAlert('Appointment created successfully!', 'success');
                setTimeout(() => {
                    window.location.href = data.redirect_url || '{% url "appointments:appointment_list" %}';
                }, 2000);
            } else {
                showAlert(data.message || 'Error creating appointment', 'error');
            }
        })
        .catch(error => {
            showLoading(false);
            console.error('Error:', error);
            showAlert('Error creating appointment', 'error');
        });
    }

    function showLoading(show) {
        document.getElementById('loadingOverlay').style.display = show ? 'flex' : 'none';
    }

    function showAlert(message, type = 'info') {
        // You can implement your preferred alert system here
        // For now, using simple alert
        if (type === 'success') {
            console.log('✅ ' + message);
        } else if (type === 'error') {
            console.log('❌ ' + message);
        } else if (type === 'warning') {
            console.log('⚠️ ' + message);
        } else {
            console.log('ℹ️ ' + message);
        }
    }

    function loadTimeSlots() {
        if (!selectedData.doctor || !selectedData.date) return;

        showLoading(true);

        fetch(`{% url 'appointments:get_available_time_slots' %}?doctor_id=${selectedData.doctor.id}&date=${selectedData.date}`)
            .then(response => response.json())
            .then(data => {
                displayTimeSlots(data.slots);
                showLoading(false);
            })
            .catch(error => {
                console.error('Error:', error);
                showLoading(false);
            });
    }

    // Make functions globally accessible
    window.showAlert = showAlert;
    window.loadTimeSlots = loadTimeSlots;

    // Load initial data
    searchPatients(''); // Load some initial patients
});
