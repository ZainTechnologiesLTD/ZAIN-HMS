// Authentication Pages JavaScript

document.addEventListener('DOMContentLoaded', function() {
    
    // Password toggle functionality
    const togglePassword = document.getElementById('togglePassword');
    if (togglePassword) {
        togglePassword.addEventListener('click', function() {
            const password = document.getElementById('id_password');
            const icon = this.querySelector('i');
            
            if (password.type === 'password') {
                password.type = 'text';
                icon.classList.remove('bi-eye');
                icon.classList.add('bi-eye-slash');
            } else {
                password.type = 'password';
                icon.classList.remove('bi-eye-slash');
                icon.classList.add('bi-eye');
            }
        });
    }

    // Password toggle for password reset confirm page
    const togglePassword1 = document.getElementById('togglePassword1');
    if (togglePassword1) {
        togglePassword1.addEventListener('click', function() {
            const password = document.getElementById('id_new_password1');
            const icon = this.querySelector('i');
            
            if (password.type === 'password') {
                password.type = 'text';
                icon.classList.remove('bi-eye');
                icon.classList.add('bi-eye-slash');
            } else {
                password.type = 'password';
                icon.classList.remove('bi-eye-slash');
                icon.classList.add('bi-eye');
            }
        });
    }

    const togglePassword2 = document.getElementById('togglePassword2');
    if (togglePassword2) {
        togglePassword2.addEventListener('click', function() {
            const password = document.getElementById('id_new_password2');
            const icon = this.querySelector('i');
            
            if (password.type === 'password') {
                password.type = 'text';
                icon.classList.remove('bi-eye');
                icon.classList.add('bi-eye-slash');
            } else {
                password.type = 'password';
                icon.classList.remove('bi-eye-slash');
                icon.classList.add('bi-eye');
            }
        });
    }

    // Form submission loading state
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            const loginText = document.getElementById('loginText');
            const loginSpinner = document.getElementById('loginSpinner');
            const loginBtn = document.getElementById('loginBtn');
            
            if (loginText && loginSpinner && loginBtn) {
                loginText.style.display = 'none';
                loginSpinner.style.display = 'inline-block';
                loginBtn.disabled = true;
            }
        });
    }

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        if (!alert.querySelector('.btn-close')) {
            setTimeout(function() {
                alert.style.opacity = '0';
                setTimeout(function() {
                    alert.remove();
                }, 300);
            }, 5000);
        }
    });

    // Form validation feedback
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;

            requiredFields.forEach(function(field) {
                if (!field.value.trim()) {
                    field.classList.add('is-invalid');
                    isValid = false;
                } else {
                    field.classList.remove('is-invalid');
                }
            });

            if (!isValid) {
                event.preventDefault();
                event.stopPropagation();
            }
        });
    });
});
