document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips for date fields
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Note: Modern date system is now handled by ultra_modern_date_picker_2025.html

    // Image preview functionality
    const imageInput = document.getElementById('{{ form.image.id_for_label }}');
    if (imageInput) {
        imageInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    // Remove existing preview
                    const existingPreview = document.querySelector('.image-preview');
                    if (existingPreview) {
                        existingPreview.remove();
                    }

                    // Create new preview
                    const img = document.createElement('img');
                    img.src = e.target.result;
                    img.className = 'image-preview d-block';
                    img.alt = 'Image preview';

                    // Insert after the file input
                    imageInput.parentNode.insertBefore(img, imageInput.nextSibling);
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // User account creation toggle
    const createAccountCheckbox = document.getElementById('{{ form.create_user_account.id_for_label }}');
    const passwordFields = document.getElementById('password-fields');

    if (createAccountCheckbox && passwordFields) {
        // Show/hide password fields based on checkbox state
        function togglePasswordFields() {
            if (createAccountCheckbox.checked) {
                passwordFields.style.display = 'block';
                // Make fields required when checkbox is checked
                document.getElementById('{{ form.username.id_for_label }}').setAttribute('required', 'required');
                document.getElementById('{{ form.password.id_for_label }}').setAttribute('required', 'required');
                document.getElementById('{{ form.confirm_password.id_for_label }}').setAttribute('required', 'required');
            } else {
                passwordFields.style.display = 'none';
                // Remove required attribute when checkbox is unchecked
                document.getElementById('{{ form.username.id_for_label }}').removeAttribute('required');
                document.getElementById('{{ form.password.id_for_label }}').removeAttribute('required');
                document.getElementById('{{ form.confirm_password.id_for_label }}').removeAttribute('required');
            }
        }

        // Initial state
        togglePasswordFields();

        // Toggle on checkbox change
        createAccountCheckbox.addEventListener('change', togglePasswordFields);
    }

    // Form validation
    const form = document.querySelector('form');
    form.addEventListener('submit', function(e) {
        let isValid = true;

        // Check required fields
        const requiredFields = form.querySelectorAll('[required]');
        requiredFields.forEach(function(field) {
            if (!field.value.trim()) {
                isValid = false;
                field.classList.add('is-invalid');
            } else {
                field.classList.remove('is-invalid');
            }
        });

        // Additional validation for password matching
        const createAccount = document.getElementById('{{ form.create_user_account.id_for_label }}');
        if (createAccount && createAccount.checked) {
            const password = document.getElementById('{{ form.password.id_for_label }}').value;
            const confirmPassword = document.getElementById('{{ form.confirm_password.id_for_label }}').value;

            if (password !== confirmPassword) {
                isValid = false;
                document.getElementById('{{ form.confirm_password.id_for_label }}').classList.add('is-invalid');
                alert('Passwords do not match.');
            }
        }

    // Date fields handled by ultra modern picker (no validation enforced)

        if (!isValid) {
            e.preventDefault();
            alert('Please fill in all required fields correctly.');
        }
    });

    // Auto-hide alerts
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            if (alert.classList.contains('alert-dismissible')) {
                const closeBtn = alert.querySelector('.btn-close');
                if (closeBtn) {
                    closeBtn.click();
                }
            }
        });
    }, 5000);
});
