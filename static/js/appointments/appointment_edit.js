    function selectPatient(patientId, patientName) {
        document.getElementById('selectedPatient').value = patientId;
        const selectedPatientInfo = document.getElementById('selectedPatientInfo');
        selectedPatientInfo.innerHTML = `Selected Patient: ${patientName}`;
        selectedPatientInfo.classList.remove('d-none');
    }

    document.addEventListener('DOMContentLoaded', function() {
        const form = document.getElementById('appointmentForm');
        const specializationSelect = document.getElementById('specialization');
        const doctorSelect = document.getElementById('doctorSelect');
        const availableSlotsSelect = document.getElementById('availableSlots');
        const appointmentTypeSelect = document.getElementById('appointmentType');
        const opdFields = document.getElementById('opd-fields');
        const errorDiv = document.getElementById('appointment-errors');

        // Handle appointment type changes
        appointmentTypeSelect.addEventListener('change', function() {
            opdFields.style.display = this.value === 'OPD' ? 'block' : 'none';
        });

        // Handle specialization changes
        specializationSelect.addEventListener('change', function() {
            if (this.value) {
                doctorSelect.disabled = false;
                doctorSelect.innerHTML = '<option value="">Select doctor</option>';
            } else {
                doctorSelect.disabled = true;
                doctorSelect.innerHTML = '<option value="">First select specialization</option>';
            }
            availableSlotsSelect.innerHTML = '<option value="">Select doctor first</option>';
        });

        // Handle doctor changes
        doctorSelect.addEventListener('change', function() {
            availableSlotsSelect.innerHTML = '<option value="">Loading available slots...</option>';
            document.getElementById('id_doctor').value = this.value;
        });

        // Form validation
        form.addEventListener('submit', function(event) {
            errorDiv.classList.add('d-none');
            errorDiv.textContent = '';

            const patientId = document.getElementById('selectedPatient').value;

            if (!patientId) {
                event.preventDefault();
                showError('Please select a patient.');
                return;
            }

            if (!doctorSelect.value) {
                event.preventDefault();
                showError('Please select a doctor.');
                return;
            }

            if (!availableSlotsSelect.value) {
                event.preventDefault();
                showError('Please select an available time slot.');
                return;
            }
        });

        function showError(message) {
            errorDiv.textContent = message;
            errorDiv.classList.remove('d-none');
            errorDiv.scrollIntoView({ behavior: 'smooth' });
        }
    });
