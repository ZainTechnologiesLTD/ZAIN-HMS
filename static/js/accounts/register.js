        // Enhanced form field handling
        document.addEventListener('DOMContentLoaded', function() {
            // This script is no longer needed as CSS handles the floating labels correctly.
            // Kept for reference or future enhancements.
        });

        // Enhanced password toggle with animation
        function setupPasswordToggle(toggleId, inputId, iconId) {
            const toggleBtn = document.getElementById(toggleId);
            const passwordInput = document.getElementById(inputId);
            const passwordIcon = document.getElementById(iconId);

            if (toggleBtn && passwordInput && passwordIcon) {
                toggleBtn.addEventListener('click', function() {
                    if (passwordInput.type === 'password') {
                        passwordInput.type = 'text';
                        passwordIcon.className = 'fas fa-eye-slash';
                        this.style.color = '#3b82f6';
                    } else {
                        passwordInput.type = 'password';
                        passwordIcon.className = 'fas fa-eye';
                        this.style.color = '#6b7280';
                    }
                });
            }
        }

        setupPasswordToggle('togglePassword1', '{{ form.password1.id_for_label }}', 'passwordIcon1');
        setupPasswordToggle('togglePassword2', '{{ form.password2.id_for_label }}', 'passwordIcon2');

        // Enhanced form submission with loading state and validation
        document.getElementById('registrationForm')?.addEventListener('submit', function(e) {
            const submitBtn = document.getElementById('registerBtn');
            const btnText = submitBtn.querySelector('.btn-text');
            const password1 = document.querySelector('input[name="password1"]');
            const password2 = document.querySelector('input[name="password2"]');

            // Basic validation
            if (password1 && password2 && password1.value !== password2.value) {
                e.preventDefault();
                showNotification('Passwords do not match.', 'error');
                return;
            }

            // Show loading state
            btnText.innerHTML = '<span class="spinner me-2"></span>{% trans "Creating Account..." %}';
            submitBtn.disabled = true;

            // Add loading animation to card
            const card = document.querySelector('.register-card');
            if (card) {
                card.style.transform = 'scale(0.98)';
                card.style.opacity = '0.8';
            }

            // Re-enable after timeout in case of error
            setTimeout(() => {
                if (submitBtn.disabled) {
                    btnText.innerHTML = '<i class="fas fa-user-plus me-2"></i>{% trans "Create Account" %}';
                    submitBtn.disabled = false;
                    if (card) {
                        card.style.transform = '';
                        card.style.opacity = '';
                    }
                }
            }, 10000);
        });

        // Notification system
        function showNotification(message, type = 'info') {
            const notification = document.createElement('div');
            notification.className = `notification notification-${type}`;
            notification.innerHTML = `
                <i class="fas ${getNotificationIcon(type)} me-2"></i>
                ${message}
            `;

            document.body.appendChild(notification);

            // Animate in
            setTimeout(() => notification.classList.add('show'), 100);

            // Auto remove
            setTimeout(() => {
                notification.classList.remove('show');
                setTimeout(() => notification.remove(), 300);
            }, 4000);
        }

        function getNotificationIcon(type) {
            const icons = {
                success: 'fa-check-circle',
                error: 'fa-exclamation-triangle',
                warning: 'fa-exclamation-circle',
                info: 'fa-info-circle'
            };
            return icons[type] || icons.info;
        }

        // Add smooth scrolling for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });

        // Add loading animation on page load
        window.addEventListener('load', function() {
            document.body.classList.add('loaded');
        });
