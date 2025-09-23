document.addEventListener('DOMContentLoaded', function() {
    const recipientTypeInputs = document.querySelectorAll('input[name="recipient_type"]');
    const customPatientsSection = document.getElementById('customPatientsSection');

    function toggleCustomPatientsSection() {
        const selectedValue = document.querySelector('input[name="recipient_type"]:checked')?.value;
        if (selectedValue === 'custom_group') {
            customPatientsSection.classList.add('show');
        } else {
            customPatientsSection.classList.remove('show');
        }
    }

    // Initial check
    toggleCustomPatientsSection();

    // Add event listeners
    recipientTypeInputs.forEach(input => {
        input.addEventListener('change', toggleCustomPatientsSection);
    });
});
