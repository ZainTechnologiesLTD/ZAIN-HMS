// Print styling
function printPrescription() {
    window.print();
}

// Add print event listener
window.addEventListener('beforeprint', function() {
    document.title = 'Prescription ' + '{{ prescription.prescription_number }}' + ' - {{ prescription.patient.get_full_name }}';
});

// Restore title after printing
window.addEventListener('afterprint', function() {
    document.title = 'Prescription {{ prescription.prescription_number }} - Dr. {{ prescription.doctor.get_full_name }}';
});
