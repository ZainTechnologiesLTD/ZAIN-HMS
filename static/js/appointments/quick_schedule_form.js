function selectPatient(patientId, patientName) {
console.log("Selected Patient ID:", patientId);
console.log("Selected Patient Name:", patientName);
// Set the selected patient ID in the hidden input
document.getElementById('selectedPatient').value = patientId;
// Display selected patient info
document.getElementById('selectedPatientInfo').innerHTML =
    `<div class="alert alert-info">Selected Patient: ${patientName}</div>`;

// Optionally, clear any previous error messages
const errorDiv = document.getElementById('appointment-errors');
errorDiv.classList.add('d-none');
errorDiv.textContent = '';
}

// Add the form submission handler once when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
document.getElementById('appointmentForm').addEventListener('submit', function(event) {
    event.preventDefault();

    // Validate patient selection
    const patientId = document.getElementById('selectedPatient').value;
    if (!patientId) {
        const errorDiv = document.getElementById('appointment-errors');
        errorDiv.classList.remove('d-none');
        errorDiv.textContent = 'Please select a patient';
        return;
    }

    // Use HTMX to submit the form
    this.submit();  // Allow HTMX to handle the submission
});
});
