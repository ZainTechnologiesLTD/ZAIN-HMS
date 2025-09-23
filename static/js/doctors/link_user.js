document.addEventListener('DOMContentLoaded', function() {
    const userOptions = document.querySelectorAll('.user-option');
    const submitBtn = document.getElementById('submitBtn');

    userOptions.forEach(option => {
        option.addEventListener('click', function() {
            // Remove selection from all options
            userOptions.forEach(opt => opt.classList.remove('selected'));

            // Add selection to clicked option
            this.classList.add('selected');

            // Check the radio button
            const radio = this.querySelector('input[type="radio"]');
            radio.checked = true;

            // Enable submit button
            submitBtn.disabled = false;
        });
    });

    // Form submission confirmation
    document.getElementById('linkUserForm')?.addEventListener('submit', function(e) {
        const selectedUser = document.querySelector('.user-option.selected .user-info h6').textContent;
        if (!confirm(`Are you sure you want to link "${selectedUser}" to Dr. {{ doctor.get_full_name }}?`)) {
            e.preventDefault();
        }
    });
});
