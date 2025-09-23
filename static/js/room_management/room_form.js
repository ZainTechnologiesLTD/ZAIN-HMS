document.addEventListener('DOMContentLoaded', function() {
    // Add Bootstrap classes to form fields
    const formFields = document.querySelectorAll('input[type="text"], input[type="number"], select');
    formFields.forEach(field => {
        field.classList.add('form-control');
    });

    // Form validation
    const form = document.querySelector('form');
    form.addEventListener('submit', function(e) {
        if (!form.checkValidity()) {
            e.preventDefault();
            e.stopPropagation();
        }
        form.classList.add('was-validated');
    });
});
