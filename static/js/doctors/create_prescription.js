let medicationCounter = 0;

document.addEventListener('DOMContentLoaded', function() {
    const patientSelect = document.getElementById('patient_id');
    const patientDetails = document.getElementById('patientDetails');
    const addMedicationBtn = document.getElementById('addMedicationBtn');
    const medicationsContainer = document.getElementById('medicationsContainer');
    const noMedicationsMsg = document.getElementById('noMedicationsMsg');
    const submitBtn = document.getElementById('submitBtn');

    // Show patient details when patient is selected
    patientSelect.addEventListener('change', function() {
        const selectedOption = this.options[this.selectedIndex];
        if (this.value) {
            document.getElementById('patientPhone').textContent = selectedOption.dataset.phone || '-';
            document.getElementById('patientEmail').textContent = selectedOption.dataset.email || '-';
            document.getElementById('patientAge').textContent = selectedOption.dataset.age || '-';
            patientDetails.style.display = 'block';
        } else {
            patientDetails.style.display = 'none';
        }
        validateForm();
    });

    // Add medication
    addMedicationBtn.addEventListener('click', function() {
        medicationCounter++;
        const template = document.getElementById('medicationTemplate');
        const clone = template.content.cloneNode(true);

        // Update medication number
        clone.querySelector('.medication-number').textContent = medicationCounter;
        clone.querySelector('.medication-counter').textContent = medicationCounter;
        clone.querySelector('.medication-item').dataset.medicationIndex = medicationCounter;

        // Add new-item class for animation
        clone.querySelector('.medication-item').classList.add('new-item');

        // Add remove functionality
        clone.querySelector('.btn-remove-medication').addEventListener('click', function() {
            this.closest('.medication-item').remove();
            renumberMedications();
            validateForm();
        });

        // Add change listeners for validation
        const inputs = clone.querySelectorAll('input[required], select[required]');
        inputs.forEach(input => {
            input.addEventListener('change', validateForm);
            input.addEventListener('input', validateForm);
        });

        medicationsContainer.appendChild(clone);
        noMedicationsMsg.style.display = 'none';

        // Remove new-item class after animation
        setTimeout(() => {
            const newItem = medicationsContainer.querySelector('.medication-item.new-item');
            if (newItem) {
                newItem.classList.remove('new-item');
            }
        }, 1000);

        validateForm();
    });

    // Renumber medications after removal
    function renumberMedications() {
        const medicationItems = medicationsContainer.querySelectorAll('.medication-item');
        medicationItems.forEach((item, index) => {
            const number = index + 1;
            item.querySelector('.medication-number').textContent = number;
            item.querySelector('.medication-counter').textContent = number;
            item.dataset.medicationIndex = number;
        });

        if (medicationItems.length === 0) {
            noMedicationsMsg.style.display = 'block';
            medicationCounter = 0;
        }
    }

    // Form validation
    function validateForm() {
        const patientSelected = patientSelect.value !== '';
        const diagnosisField = document.getElementById('diagnosis');
        const diagnosisFilled = diagnosisField.value.trim() !== '';
        const medicationItems = medicationsContainer.querySelectorAll('.medication-item');

        let medicationsValid = medicationItems.length > 0;

        // Check if all required fields in medications are filled
        medicationItems.forEach(item => {
            const requiredFields = item.querySelectorAll('input[required], select[required]');
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    medicationsValid = false;
                }
            });
        });

        const isValid = patientSelected && diagnosisFilled && medicationsValid;
        submitBtn.disabled = !isValid;

        if (isValid) {
            submitBtn.classList.remove('btn-outline-primary');
            submitBtn.classList.add('btn-primary');
        } else {
            submitBtn.classList.remove('btn-primary');
            submitBtn.classList.add('btn-outline-primary');
        }
    }

    // Add validation listeners to existing fields
    patientSelect.addEventListener('change', validateForm);
    document.getElementById('diagnosis').addEventListener('input', validateForm);

    // Form submission
    document.getElementById('prescriptionForm').addEventListener('submit', function(e) {
        if (submitBtn.disabled) {
            e.preventDefault();
            alert('Please fill in all required fields before submitting.');
            return;
        }

        // Show loading state
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Creating Prescription...';
        submitBtn.disabled = true;
    });

    // Initial validation
    validateForm();
});
