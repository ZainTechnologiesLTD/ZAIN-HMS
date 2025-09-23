document.addEventListener('DOMContentLoaded', function() {
    // Add confirmation for creating user accounts
    document.querySelectorAll('.create-user-form').forEach(form => {
        form.addEventListener('submit', function(e) {
            const doctorName = this.closest('.doctor-card').querySelector('h6').textContent;
            if (!confirm(`Create a user account for ${doctorName}? An email with login credentials will be sent to their email address.`)) {
                e.preventDefault();
            }
        });
    });
});
