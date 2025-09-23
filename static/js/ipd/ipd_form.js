document.addEventListener('DOMContentLoaded', function() {
    // Initialize form for edit mode
    const patientInitialValue = '{{ form.patient.value|default:"" }}';
    const attendingDoctorInitialValue = '{{ form.attending_doctor.value|default:"" }}';
    const referringDoctorInitialValue = '{{ form.referring_doctor.value|default:"" }}';

    // Patient Search Functionality
    let patientSearchTimeout;
    const patientSearchInput = document.getElementById('patient-search');
    const patientResults = document.getElementById('patient-results');
    const patientLoading = document.getElementById('patient-loading');
    const selectedPatient = document.getElementById('selected-patient');
    const patientHiddenField = document.getElementById('id_patient');

    patientSearchInput.addEventListener('input', function() {
        const term = this.value.trim();

        if (term.length < 2) {
            patientResults.style.display = 'none';
            return;
        }

        clearTimeout(patientSearchTimeout);
        patientSearchTimeout = setTimeout(() => searchPatients(term), 300);
    });

    function searchPatients(term) {
        patientLoading.style.display = 'block';
        patientResults.style.display = 'block';
        patientResults.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i> Searching patients...</div>';

        fetch(`{% url "ipd:ajax_search_patients" %}?term=${encodeURIComponent(term)}`)
            .then(response => response.json())
            .then(data => {
                patientResults.innerHTML = '';

                if (data.results && data.results.length > 0) {
                    data.results.forEach(patient => {
                        const item = document.createElement('div');
                        item.className = 'search-result-item';
                        item.innerHTML = `
                            <div class="search-result-name">${patient.full_name}</div>
                            <div class="search-result-details">ID: ${patient.patient_id} | Phone: ${patient.phone || 'N/A'}</div>
                        `;
                        item.addEventListener('click', () => selectPatient(patient));
                        patientResults.appendChild(item);
                    });
                } else {
                    patientResults.innerHTML = '<div class="no-results">No patients found</div>';
                }

                patientLoading.style.display = 'none';
            })
            .catch(error => {
                console.error('Error:', error);
                patientResults.innerHTML = '<div class="no-results">Error searching patients</div>';
                patientLoading.style.display = 'none';
            });
    }

    function selectPatient(patient) {
        // Set hidden field value
        patientHiddenField.value = patient.id;

        // Show selected patient
        document.getElementById('selected-patient-name').textContent = patient.full_name;
        document.getElementById('selected-patient-details').textContent = `ID: ${patient.patient_id} | Phone: ${patient.phone || 'N/A'}`;
        selectedPatient.style.display = 'block';

        // Hide search results and clear search
        patientResults.style.display = 'none';
        patientSearchInput.value = '';
        patientSearchInput.style.display = 'none';
    }

    // Remove patient selection
    selectedPatient.querySelector('.remove-selection').addEventListener('click', function() {
        patientHiddenField.value = '';
        selectedPatient.style.display = 'none';
        patientSearchInput.style.display = 'block';
        patientSearchInput.focus();
    });

    // Doctor Search Functionality
    let doctorSearchTimeout;
    const doctorSearchInput = document.getElementById('doctor-search');
    const doctorResults = document.getElementById('doctor-results');
    const doctorLoading = document.getElementById('doctor-loading');
    const selectedDoctor = document.getElementById('selected-doctor');
    const doctorHiddenField = document.getElementById('id_attending_doctor');

    doctorSearchInput.addEventListener('input', function() {
        const term = this.value.trim();

        if (term.length < 2) {
            doctorResults.style.display = 'none';
            return;
        }

        clearTimeout(doctorSearchTimeout);
        doctorSearchTimeout = setTimeout(() => searchDoctors(term), 300);
    });

    function searchDoctors(term) {
        doctorLoading.style.display = 'block';
        doctorResults.style.display = 'block';
        doctorResults.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i> Searching doctors...</div>';

        fetch(`{% url "ipd:ajax_search_doctors" %}?term=${encodeURIComponent(term)}`)
            .then(response => response.json())
            .then(data => {
                doctorResults.innerHTML = '';

                if (data.results && data.results.length > 0) {
                    data.results.forEach(doctor => {
                        const item = document.createElement('div');
                        item.className = 'search-result-item';
                        item.innerHTML = `
                            <div class="search-result-name">Dr. ${doctor.full_name}</div>
                            <div class="search-result-details">Specialization: ${doctor.specialization || 'General'}</div>
                        `;
                        item.addEventListener('click', () => selectDoctor(doctor));
                        doctorResults.appendChild(item);
                    });
                } else {
                    doctorResults.innerHTML = '<div class="no-results">No doctors found</div>';
                }

                doctorLoading.style.display = 'none';
            })
            .catch(error => {
                console.error('Error:', error);
                doctorResults.innerHTML = '<div class="no-results">Error searching doctors</div>';
                doctorLoading.style.display = 'none';
            });
    }

    function selectDoctor(doctor) {
        // Set hidden field value
        doctorHiddenField.value = doctor.id;

        // Show selected doctor
        document.getElementById('selected-doctor-name').textContent = `Dr. ${doctor.full_name}`;
        document.getElementById('selected-doctor-details').textContent = `Specialization: ${doctor.specialization || 'General'}`;
        selectedDoctor.style.display = 'block';

        // Hide search results and clear search
        doctorResults.style.display = 'none';
        doctorSearchInput.value = '';
        doctorSearchInput.style.display = 'none';
    }

    // Remove doctor selection
    selectedDoctor.querySelector('.remove-selection').addEventListener('click', function() {
        doctorHiddenField.value = '';
        selectedDoctor.style.display = 'none';
        doctorSearchInput.style.display = 'block';
        doctorSearchInput.focus();
    });

    // Referring Doctor Search Functionality
    let referringDoctorSearchTimeout;
    const referringDoctorSearchInput = document.getElementById('referring-doctor-search');
    const referringDoctorResults = document.getElementById('referring-doctor-results');
    const referringDoctorLoading = document.getElementById('referring-doctor-loading');
    const selectedReferringDoctor = document.getElementById('selected-referring-doctor');
    const referringDoctorHiddenField = document.getElementById('id_referring_doctor');

    referringDoctorSearchInput.addEventListener('input', function() {
        const term = this.value.trim();

        if (term.length < 2) {
            referringDoctorResults.style.display = 'none';
            return;
        }

        clearTimeout(referringDoctorSearchTimeout);
        referringDoctorSearchTimeout = setTimeout(() => searchReferringDoctors(term), 300);
    });

    function searchReferringDoctors(term) {
        referringDoctorLoading.style.display = 'block';
        referringDoctorResults.style.display = 'block';
        referringDoctorResults.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i> Searching doctors...</div>';

        fetch(`{% url "ipd:ajax_search_doctors" %}?term=${encodeURIComponent(term)}`)
            .then(response => response.json())
            .then(data => {
                referringDoctorResults.innerHTML = '';

                if (data.results && data.results.length > 0) {
                    data.results.forEach(doctor => {
                        const item = document.createElement('div');
                        item.className = 'search-result-item';
                        item.innerHTML = `
                            <div class="search-result-name">Dr. ${doctor.full_name}</div>
                            <div class="search-result-details">Specialization: ${doctor.specialization || 'General'}</div>
                        `;
                        item.addEventListener('click', () => selectReferringDoctor(doctor));
                        referringDoctorResults.appendChild(item);
                    });
                } else {
                    referringDoctorResults.innerHTML = '<div class="no-results">No doctors found</div>';
                }

                referringDoctorLoading.style.display = 'none';
            })
            .catch(error => {
                console.error('Error:', error);
                referringDoctorResults.innerHTML = '<div class="no-results">Error searching doctors</div>';
                referringDoctorLoading.style.display = 'none';
            });
    }

    function selectReferringDoctor(doctor) {
        // Set hidden field value
        referringDoctorHiddenField.value = doctor.id;

        // Show selected doctor
        document.getElementById('selected-referring-doctor-name').textContent = `Dr. ${doctor.full_name}`;
        document.getElementById('selected-referring-doctor-details').textContent = `Specialization: ${doctor.specialization || 'General'}`;
        selectedReferringDoctor.style.display = 'block';

        // Hide search results and clear search
        referringDoctorResults.style.display = 'none';
        referringDoctorSearchInput.value = '';
        referringDoctorSearchInput.style.display = 'none';
    }

    // Remove referring doctor selection
    selectedReferringDoctor.querySelector('.remove-selection').addEventListener('click', function() {
        referringDoctorHiddenField.value = '';
        selectedReferringDoctor.style.display = 'none';
        referringDoctorSearchInput.style.display = 'block';
        referringDoctorSearchInput.focus();
    });

    // Hide search results when clicking outside
    document.addEventListener('click', function(event) {
        if (!patientSearchInput.contains(event.target) && !patientResults.contains(event.target)) {
            patientResults.style.display = 'none';
        }
        if (!doctorSearchInput.contains(event.target) && !doctorResults.contains(event.target)) {
            doctorResults.style.display = 'none';
        }
        if (!referringDoctorSearchInput.contains(event.target) && !referringDoctorResults.contains(event.target)) {
            referringDoctorResults.style.display = 'none';
        }
    });

    // Room change handler for bed filtering
    const roomSelect = document.getElementById('id_room');
    const bedSelect = document.getElementById('id_bed');

    if (roomSelect) {
        bedSelect.disabled = true;

        roomSelect.addEventListener('change', function() {
            const roomId = this.value;

            if (roomId) {
                bedSelect.disabled = false;
                bedSelect.innerHTML = '<option value="">Loading available beds...</option>';

                fetch(`{% url "ipd:ajax_get_available_beds" %}?room_id=${roomId}`)
                    .then(response => response.json())
                    .then(data => {
                        bedSelect.innerHTML = '<option value="">Select an available bed...</option>';

                        if (data.results && data.results.length > 0) {
                            data.results.forEach(bed => {
                                bedSelect.innerHTML += `<option value="${bed.id}">Bed ${bed.number}</option>`;
                            });
                        } else {
                            bedSelect.innerHTML = '<option value="" disabled>No available beds in this room</option>';
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        bedSelect.innerHTML = '<option value="" disabled>Error loading beds</option>';
                    });
            } else {
                bedSelect.disabled = true;
                bedSelect.innerHTML = '<option value="">First select a room...</option>';
            }
        });
    }

    // Form validation
    const form = document.querySelector('form');
    form.addEventListener('submit', function(e) {
        const patient = patientHiddenField.value;
        const doctor = doctorHiddenField.value;
        const room = roomSelect.value;
        const bed = bedSelect.value;

        if (!patient) {
            e.preventDefault();
            alert('Please search and select a patient.');
            patientSearchInput.focus();
            return false;
        }

        if (!doctor) {
            e.preventDefault();
            alert('Please search and select an attending doctor.');
            doctorSearchInput.focus();
            return false;
        }

        if (!room) {
            e.preventDefault();
            alert('Please select a room.');
            roomSelect.focus();
            return false;
        }

        if (!bed) {
            e.preventDefault();
            alert('Please select an available bed.');
            bedSelect.focus();
            return false;
        }
    });
});
