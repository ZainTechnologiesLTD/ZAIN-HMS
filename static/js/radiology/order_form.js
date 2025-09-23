document.addEventListener('DOMContentLoaded', function() {
    const studyCheckboxes = document.querySelectorAll('.study-checkbox');
    const submitBtn = document.getElementById('submitOrderBtn');
    const selectedSummary = document.getElementById('selectedStudiesSummary');
    const selectedList = document.getElementById('selectedStudiesList');
    const totalStudiesSpan = document.getElementById('totalStudies');
    const totalCostSpan = document.getElementById('totalCost');
    const hiddenFieldsContainer = document.getElementById('hiddenStudyFields');

    // Enhanced search elements
    const patientSearchInput = document.getElementById('patientSearchInput');
    const doctorSearchInput = document.getElementById('doctorSearchInput');
    const patientDropdown = document.getElementById('patientDropdown');
    const doctorDropdown = document.getElementById('doctorDropdown');
    const patientSelect = document.getElementById('{{ form.patient.id_for_label }}');
    const doctorSelect = document.getElementById('{{ form.ordering_doctor.id_for_label }}');
    const clearPatientBtn = document.getElementById('clearPatientBtn');
    const clearDoctorBtn = document.getElementById('clearDoctorBtn');
    const selectedPatient = document.getElementById('selectedPatient');
    const selectedDoctor = document.getElementById('selectedDoctor');
    const selectedPatientInfo = document.getElementById('selectedPatientInfo');
    const selectedDoctorInfo = document.getElementById('selectedDoctorInfo');

    let selectedStudies = [];
    let patientOptions = [];
    let doctorOptions = [];

    // Study type data
    const studyTypes = {
        {% for study_type in study_types %}
        {{ study_type.id }}: {
            name: "{{ study_type.name|escapejs }}",
            code: "{{ study_type.code|escapejs }}",
            modality: "{{ study_type.modality|escapejs }}",
            price: {{ study_type.price|default:"0" }}
        },
        {% endfor %}
    };

    // Initialize patient and doctor options
    function initializeOptions() {
        // Get patient options
        if (patientSelect) {
            patientOptions = Array.from(patientSelect.options).map(option => ({
                value: option.value,
                text: option.text,
                element: option
            })).filter(opt => opt.value); // Remove empty option
        }

        // Get doctor options
        if (doctorSelect) {
            doctorOptions = Array.from(doctorSelect.options).map(option => ({
                value: option.value,
                text: option.text,
                element: option
            })).filter(opt => opt.value); // Remove empty option
        }
    }

    // Enhanced Patient Search
    function setupPatientSearch() {
        if (!patientSearchInput || !patientDropdown) return;

        patientSearchInput.addEventListener('focus', function() {
            showPatientDropdown();
        });

        patientSearchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase().trim();
            filterAndShowPatients(searchTerm);
        });

        patientSearchInput.addEventListener('blur', function() {
            // Delay hiding to allow for clicks
            setTimeout(() => {
                patientDropdown.style.display = 'none';
            }, 150);
        });

        clearPatientBtn.addEventListener('click', function() {
            clearPatientSelection();
        });
    }

    function filterAndShowPatients(searchTerm) {
        patientDropdown.innerHTML = '';

        const filteredPatients = patientOptions.filter(patient =>
            patient.text.toLowerCase().includes(searchTerm)
        );

        if (filteredPatients.length === 0) {
            patientDropdown.innerHTML = '<div class="dropdown-item-text text-muted">No patients found</div>';
        } else {
            filteredPatients.slice(0, 10).forEach(patient => { // Limit to 10 results
                const item = document.createElement('div');
                item.className = 'dropdown-item';
                item.style.cursor = 'pointer';
                item.innerHTML = `<i class="fas fa-user-injured me-2"></i>${patient.text}`;
                item.addEventListener('click', function() {
                    selectPatient(patient);
                });
                patientDropdown.appendChild(item);
            });
        }

        patientDropdown.style.display = 'block';
    }

    function showPatientDropdown() {
        if (patientOptions.length === 0) return;

        patientDropdown.innerHTML = '';
        patientOptions.slice(0, 10).forEach(patient => {
            const item = document.createElement('div');
            item.className = 'dropdown-item';
            item.style.cursor = 'pointer';
            item.innerHTML = `<i class="fas fa-user-injured me-2"></i>${patient.text}`;
            item.addEventListener('click', function() {
                selectPatient(patient);
            });
            patientDropdown.appendChild(item);
        });

        patientDropdown.style.display = 'block';
    }

    function selectPatient(patient) {
        patientSearchInput.value = patient.text;
        patientSelect.value = patient.value;
        selectedPatientInfo.textContent = patient.text;
        selectedPatient.style.display = 'block';
        clearPatientBtn.style.display = 'block';
        patientDropdown.style.display = 'none';

        // Trigger change event
        patientSelect.dispatchEvent(new Event('change'));
    }

    function clearPatientSelection() {
        patientSearchInput.value = '';
        patientSelect.value = '';
        selectedPatient.style.display = 'none';
        clearPatientBtn.style.display = 'none';
        patientDropdown.style.display = 'none';
        patientSearchInput.focus();
    }

    // Enhanced Doctor Search
    function setupDoctorSearch() {
        if (!doctorSearchInput || !doctorDropdown) return;

        doctorSearchInput.addEventListener('focus', function() {
            showDoctorDropdown();
        });

        doctorSearchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase().trim();
            filterAndShowDoctors(searchTerm);
        });

        doctorSearchInput.addEventListener('blur', function() {
            // Delay hiding to allow for clicks
            setTimeout(() => {
                doctorDropdown.style.display = 'none';
            }, 150);
        });

        clearDoctorBtn.addEventListener('click', function() {
            clearDoctorSelection();
        });
    }

    function filterAndShowDoctors(searchTerm) {
        doctorDropdown.innerHTML = '';

        const filteredDoctors = doctorOptions.filter(doctor =>
            doctor.text.toLowerCase().includes(searchTerm)
        );

        if (filteredDoctors.length === 0) {
            doctorDropdown.innerHTML = '<div class="dropdown-item-text text-muted">No doctors found</div>';
        } else {
            filteredDoctors.slice(0, 10).forEach(doctor => { // Limit to 10 results
                const item = document.createElement('div');
                item.className = 'dropdown-item';
                item.style.cursor = 'pointer';
                item.innerHTML = `<i class="fas fa-user-md me-2"></i>${doctor.text}`;
                item.addEventListener('click', function() {
                    selectDoctor(doctor);
                });
                doctorDropdown.appendChild(item);
            });
        }

        doctorDropdown.style.display = 'block';
    }

    function showDoctorDropdown() {
        if (doctorOptions.length === 0) return;

        doctorDropdown.innerHTML = '';
        doctorOptions.slice(0, 10).forEach(doctor => {
            const item = document.createElement('div');
            item.className = 'dropdown-item';
            item.style.cursor = 'pointer';
            item.innerHTML = `<i class="fas fa-user-md me-2"></i>${doctor.text}`;
            item.addEventListener('click', function() {
                selectDoctor(doctor);
            });
            doctorDropdown.appendChild(item);
        });

        doctorDropdown.style.display = 'block';
    }

    function selectDoctor(doctor) {
        doctorSearchInput.value = doctor.text;
        doctorSelect.value = doctor.value;
        selectedDoctorInfo.textContent = doctor.text;
        selectedDoctor.style.display = 'block';
        clearDoctorBtn.style.display = 'block';
        doctorDropdown.style.display = 'none';

        // Trigger change event
        doctorSelect.dispatchEvent(new Event('change'));
    }

    function clearDoctorSelection() {
        doctorSearchInput.value = '';
        doctorSelect.value = '';
        selectedDoctor.style.display = 'none';
        clearDoctorBtn.style.display = 'none';
        doctorDropdown.style.display = 'none';
        doctorSearchInput.focus();
    }

    // Close dropdowns when clicking outside
    document.addEventListener('click', function(event) {
        if (!event.target.closest('#patientSearchInput') && !event.target.closest('#patientDropdown')) {
            patientDropdown.style.display = 'none';
        }
        if (!event.target.closest('#doctorSearchInput') && !event.target.closest('#doctorDropdown')) {
            doctorDropdown.style.display = 'none';
        }
    });

    // Update modality counts
    function updateModalityCounts() {
        const modalities = ['X_RAY', 'CT', 'MRI', 'ULTRASOUND', 'MAMMOGRAPHY'];
        const modalityNames = {
            'X_RAY': 'xray',
            'CT': 'ct',
            'MRI': 'mri',
            'ULTRASOUND': 'ultrasound',
            'MAMMOGRAPHY': 'mammography'
        };

        modalities.forEach(modality => {
            const modalityName = modalityNames[modality];
            const checkedBoxes = document.querySelectorAll(
                `.study-checkbox[data-modality="${modality}"]:checked`
            );
            const count = checkedBoxes ? checkedBoxes.length : 0;
            const countElement = document.getElementById(`${modalityName}-count`);
            if (countElement) {
                countElement.textContent = count;
                countElement.className = count > 0 ? 'badge bg-success ms-1' : 'badge bg-secondary ms-1';
            }

            // Show/hide empty message
            const studiesContainer = document.getElementById(`${modalityName}-studies`);
            const emptyMessage = document.getElementById(`${modalityName}-empty`);
            if (studiesContainer && emptyMessage) {
                const hasStudies = studiesContainer.children.length > 0;
                emptyMessage.style.display = hasStudies ? 'none' : 'block';
            }
        });

        // Update "other" count
        const otherChecked = document.querySelectorAll('.study-checkbox:checked').length -
                           modalities.reduce((sum, mod) => {
                               const boxes = document.querySelectorAll(`.study-checkbox[data-modality="${mod}"]:checked`);
                               return sum + (boxes ? boxes.length : 0);
                           }, 0);
        const otherCountElement = document.getElementById('other-count');
        if (otherCountElement) {
            otherCountElement.textContent = Math.max(0, otherChecked);
            otherCountElement.className = otherChecked > 0 ? 'badge bg-success ms-1' : 'badge bg-secondary ms-1';
        }
    }

    function updateSelectedStudies() {
        selectedStudies = [];
        let totalCost = 0;

        studyCheckboxes.forEach(checkbox => {
            if (checkbox.checked) {
                const studyId = parseInt(checkbox.value);
                const lateralitySelect = document.querySelector(`select[name="laterality_${studyId}"]`);
                const laterality = lateralitySelect ? lateralitySelect.value : '';

                selectedStudies.push({
                    id: studyId,
                    laterality: laterality,
                    ...studyTypes[studyId]
                });

                totalCost += studyTypes[studyId].price;
            }
        });

        // Update UI
        if (selectedStudies.length > 0) {
            selectedSummary.style.display = 'block';
            submitBtn.disabled = false;

            // Update summary
            selectedList.innerHTML = selectedStudies.map(study => `
                <div class="d-flex justify-content-between align-items-center border-bottom py-2">
                    <div>
                        <strong>${study.name}</strong> (${study.code})
                        ${study.laterality ? `<br><small class="text-muted">Laterality: ${study.laterality}</small>` : ''}
                    </div>
                    <div class="text-end">
                        <span class="badge bg-info">${study.modality}</span>
                        <br><small class="text-success">$${study.price}</small>
                    </div>
                </div>
            `).join('');

            totalStudiesSpan.textContent = selectedStudies.length;
            totalCostSpan.textContent = totalCost.toFixed(2);
        } else {
            selectedSummary.style.display = 'none';
            submitBtn.disabled = true;
        }

        // Update hidden form fields
        updateHiddenFields();

        // Update modality counts
        updateModalityCounts();
    }

    function updateHiddenFields() {
        hiddenFieldsContainer.innerHTML = '';

        selectedStudies.forEach((study, index) => {
            // Create hidden fields for each selected study
            const studyIdField = document.createElement('input');
            studyIdField.type = 'hidden';
            studyIdField.name = `studies[${index}][study_type]`;
            studyIdField.value = study.id;

            const lateralityField = document.createElement('input');
            lateralityField.type = 'hidden';
            lateralityField.name = `studies[${index}][laterality]`;
            lateralityField.value = study.laterality || '';

            hiddenFieldsContainer.appendChild(studyIdField);
            hiddenFieldsContainer.appendChild(lateralityField);
        });
    }

    // Event listeners for study selection
    studyCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const studyCard = this.closest('.study-type-card');
            const lateralitySection = studyCard.querySelector('.laterality-section');

            if (this.checked) {
                studyCard.classList.add('border-success');
                lateralitySection.style.display = 'block';
            } else {
                studyCard.classList.remove('border-success');
                lateralitySection.style.display = 'none';
            }

            updateSelectedStudies();
        });
    });

    // Laterality change listener
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('laterality-select')) {
            updateSelectedStudies();
        }
    });

    // Form validation
    document.getElementById('radiologyOrderForm').addEventListener('submit', function(e) {
        if (selectedStudies.length === 0) {
            e.preventDefault();
            alert('Please select at least one study for this radiology order.');
            return false;
        }
    });

    // Initialize everything
    initializeOptions();
    setupPatientSearch();
    setupDoctorSearch();
    updateModalityCounts();
    updateSelectedStudies();
});
