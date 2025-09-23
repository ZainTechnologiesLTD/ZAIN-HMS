document.addEventListener('DOMContentLoaded', function() {
    // Add confirmation prompt for extra safety
    const deleteForm = document.querySelector('form[method="post"]');
    const submitButton = deleteForm.querySelector('button[type="submit"]');

    submitButton.addEventListener('click', function(e) {
        e.preventDefault();

        // Show native confirmation dialog
        const patientName = "{{ object.get_full_name|escapejs }}";
        const confirmed = confirm(
            `Are you absolutely sure you want to deactivate ${patientName}?\n\n` +
            'This will:\n' +
            '• Hide the patient from active lists\n' +
            '• Cancel upcoming appointments\n' +
            '• Preserve all medical records\n\n' +
            'Click OK to proceed or Cancel to abort.'
        );

        if (confirmed) {
            // Show loading state
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Deactivating...';
            submitButton.disabled = true;

            // Submit the form
            deleteForm.submit();
        }
    });
});
