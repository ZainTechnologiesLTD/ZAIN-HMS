document.addEventListener('DOMContentLoaded', function() {
    // Set today as default date for joining_date if empty
    const dateJoinedInput = document.getElementById('{{ form.joining_date.id_for_label }}');
    if (dateJoinedInput && !dateJoinedInput.value) {
        const today = new Date();
        const formattedDate = String(today.getDate()).padStart(2, '0') + '/' +
                              String(today.getMonth() + 1).padStart(2, '0') + '/' +
                              today.getFullYear();
        if (window.flatpickr && dateJoinedInput._flatpickr) {
            dateJoinedInput._flatpickr.setDate(formattedDate, true);
        } else {
            dateJoinedInput.value = formattedDate;
        }
    }

    // Get form elements
    const createAccountCheckbox = document.getElementById('{{ form.create_user_account.id_for_label }}');
    const accountFields = document.getElementById('account-fields');
    const usernameInput = document.getElementById('{{ form.username.id_for_label }}');
    const passwordInput = document.getElementById('{{ form.password.id_for_label }}');
    const passwordConfirmInput = document.getElementById('{{ form.password_confirm.id_for_label }}');
    const firstNameField = document.getElementById('{{ form.first_name.id_for_label }}');
    const lastNameField = document.getElementById('{{ form.last_name.id_for_label }}');
    const suggestionDiv = document.getElementById('username-suggestions');
    const suggestionList = document.getElementById('suggestion-list');
    const feedbackDiv = document.querySelector('.username-feedback');
    const passwordStrengthDiv = document.querySelector('.password-strength');

    // Initialize account creation as checked
    if (createAccountCheckbox) {
        createAccountCheckbox.checked = true;
    }

    function toggleAccountFields() {
        if (createAccountCheckbox && createAccountCheckbox.checked) {
            accountFields.style.display = 'flex';
            if (usernameInput) usernameInput.required = true;
            {% if not object.pk %}
            if (passwordInput) passwordInput.required = true;
            if (passwordConfirmInput) passwordConfirmInput.required = true;
            {% endif %}
        } else {
            accountFields.style.display = 'none';
            if (usernameInput) usernameInput.required = false;
            if (passwordInput) passwordInput.required = false;
            if (passwordConfirmInput) passwordConfirmInput.required = false;
            if (suggestionDiv) suggestionDiv.style.display = 'none';
        }
    }

    function generateUsernameSuggestions() {
        const firstName = firstNameField ? firstNameField.value.toLowerCase().trim() : '';
        const lastName = lastNameField ? lastNameField.value.toLowerCase().trim() : '';

        if (firstName && lastName && createAccountCheckbox && createAccountCheckbox.checked) {
            const suggestions = [
                `${firstName}.${lastName}`,
                `${firstName[0]}.${lastName}`,
                `${firstName}.${lastName[0]}`,
                `${firstName}_${lastName}`,
                `${lastName}.${firstName}`,
                `${firstName}${lastName}`,
                `${firstName}.${lastName}2`,
                `${firstName}.${lastName}3`
            ];

            const currentUsername = usernameInput ? usernameInput.value.toLowerCase() : '';
            const uniqueSuggestions = [...new Set(suggestions)]
                .filter(s => s !== currentUsername && s.length >= 3)
                .slice(0, 6);

            if (uniqueSuggestions.length > 0 && suggestionList) {
                suggestionList.innerHTML = uniqueSuggestions.map(s =>
                    `<span class="username-suggestion">${s}</span>`
                ).join('');
                suggestionDiv.style.display = 'block';
            } else if (suggestionDiv) {
                suggestionDiv.style.display = 'none';
            }
        } else if (suggestionDiv) {
            suggestionDiv.style.display = 'none';
        }
    }

    function checkPasswordStrength(password) {
        if (!passwordStrengthDiv) return;

        if (!password) {
            passwordStrengthDiv.innerHTML = '';
            return;
        }

        let strength = 0;
        let feedback = [];

        if (password.length >= 8) strength++;
        else feedback.push('At least 8 characters');

        if (/[a-z]/.test(password)) strength++;
        else feedback.push('Lowercase letter');

        if (/[A-Z]/.test(password)) strength++;
        else feedback.push('Uppercase letter');

        if (/[0-9]/.test(password)) strength++;
        else feedback.push('Number');

        if (/[^A-Za-z0-9]/.test(password)) strength++;
        else feedback.push('Special character');

        const strengthLevels = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong'];
        const strengthColors = ['danger', 'warning', 'info', 'primary', 'success'];
        const strengthLevel = strengthLevels[Math.min(strength, 4)];
        const strengthColor = strengthColors[Math.min(strength, 4)];

        let html = `<div class="progress" style="height: 8px;">
            <div class="progress-bar bg-${strengthColor}" style="width: ${(strength / 5) * 100}%"></div>
        </div>
        <small class="text-${strengthColor} fw-bold">Password Strength: ${strengthLevel}</small>`;

        if (feedback.length > 0) {
            html += `<div class="small text-muted mt-1">Missing: ${feedback.join(', ')}</div>`;
        }

        passwordStrengthDiv.innerHTML = html;
    }

    // Event listeners
    if (createAccountCheckbox) {
        createAccountCheckbox.addEventListener('change', function() {
            toggleAccountFields();
            generateUsernameSuggestions();
        });
        toggleAccountFields(); // Set initial state
    }

    if (firstNameField && lastNameField) {
        firstNameField.addEventListener('input', generateUsernameSuggestions);
        lastNameField.addEventListener('input', generateUsernameSuggestions);
        firstNameField.addEventListener('blur', generateUsernameSuggestions);
        lastNameField.addEventListener('blur', generateUsernameSuggestions);
    }

    // Username validation with improved feedback
    let validationTimeout;
    if (usernameInput && feedbackDiv) {
        usernameInput.addEventListener('input', function() {
            const username = this.value.trim();
            clearTimeout(validationTimeout);

            if (username.length === 0) {
                feedbackDiv.innerHTML = '<small class="text-muted"><i class="fas fa-info-circle me-1"></i>Username is required</small>';
                return;
            }

            if (username.length < 3) {
                feedbackDiv.innerHTML = '<small class="text-muted"><i class="fas fa-exclamation-circle me-1"></i>Enter at least 3 characters</small>';
                return;
            }

            feedbackDiv.innerHTML = '<small class="text-info"><i class="fas fa-spinner fa-spin me-1"></i>Checking availability...</small>';

            validationTimeout = setTimeout(() => {
                checkUsernameAvailability(username);
            }, 500);
        });
    }

    // Password strength checking
    if (passwordInput) {
        passwordInput.addEventListener('input', function() {
            checkPasswordStrength(this.value);
        });
    }

    function checkUsernameAvailability(username) {
        if (!feedbackDiv) return;

        fetch(`{% url 'staff:check_username' %}?username=${encodeURIComponent(username)}`)
            .then(response => response.json())
            .then(data => {
                if (data.available) {
                    feedbackDiv.innerHTML = '<small class="text-success"><i class="fas fa-check-circle me-1"></i>Username is available</small>';
                } else {
                    let suggestionsHtml = '';
                    if (data.suggestions && data.suggestions.length > 0) {
                        suggestionsHtml = '<div class="mt-2"><small class="text-muted">Try: ';
                        suggestionsHtml += data.suggestions.map(s => `<span class="username-suggestion">${s}</span>`).join(' ');
                        suggestionsHtml += '</small></div>';
                    }
                    feedbackDiv.innerHTML = `<small class="text-danger"><i class="fas fa-times-circle me-1"></i>${data.message}</small>${suggestionsHtml}`;
                }
            })
            .catch(error => {
                console.error('Username validation error:', error);
                feedbackDiv.innerHTML = '<small class="text-warning"><i class="fas fa-exclamation-triangle me-1"></i>Could not verify username</small>';
            });
    }

    // Handle suggestion clicks (both from input suggestions and validation feedback)
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('username-suggestion')) {
            e.preventDefault();
            const suggestedUsername = e.target.textContent.trim();
            if (usernameInput) {
                usernameInput.value = suggestedUsername;
                if (suggestionDiv) suggestionDiv.style.display = 'none';
                usernameInput.dispatchEvent(new Event('input'));
                usernameInput.focus();
            }
        }
    });

    // Hide suggestions when username field is focused
    if (usernameInput) {
        usernameInput.addEventListener('focus', function() {
            if (suggestionDiv) {
                setTimeout(() => suggestionDiv.style.display = 'none', 100);
            }
        });
    }

    // Role-based Staff ID preview with enhanced styling
    const roleSelect = document.getElementById('{{ form.role.id_for_label }}');
    if (roleSelect) {
        function updateStaffIdPreview() {
            const selectedRole = roleSelect.value;
            const rolePrefixes = {
                'NURSE': 'NUR', 'PHARMACIST': 'PHA', 'LAB_TECHNICIAN': 'LAB',
                'RADIOLOGIST': 'RAD', 'ACCOUNTANT': 'ACC', 'HR_MANAGER': 'HRM',
                'RECEPTIONIST': 'REC', 'STAFF': 'STF'
            };

            const prefix = rolePrefixes[selectedRole] || 'STF';
            const currentYear = new Date().getFullYear();
            const preview = `${prefix}-${currentYear}-XXXXXXXX`;

            const previewElement = document.getElementById('staff-id-preview');
            if (previewElement) {
                if (selectedRole) {
                    previewElement.innerHTML = `
                        <div class="d-flex align-items-center justify-content-between">
                            <span><i class="fas fa-id-badge text-primary me-2"></i>Staff ID will be:</span>
                            <span class="badge bg-primary fs-6">${preview}</span>
                        </div>
                    `;
                    previewElement.className = 'mt-2 p-3 bg-light border border-primary rounded';
                } else {
                    previewElement.innerHTML = '<small class="text-muted"><i class="fas fa-info-circle me-1"></i>Select a role to generate Staff ID</small>';
                    previewElement.className = 'mt-2 p-2 bg-light rounded';
                }
            }
        }

        roleSelect.addEventListener('change', updateStaffIdPreview);
        if (roleSelect.value) {
            updateStaffIdPreview();
        }
    }

    // Add smooth scrolling to form sections
    function scrollToFirstError() {
        const firstError = document.querySelector('.text-danger');
        if (firstError) {
            firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    // Form validation feedback
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('input[required], select[required], textarea[required]');
            let hasErrors = false;

            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    hasErrors = true;
                    field.classList.add('is-invalid');
                } else {
                    field.classList.remove('is-invalid');
                }
            });

            if (hasErrors) {
                e.preventDefault();
                scrollToFirstError();

                // Show a toast-like notification
                const alertDiv = document.createElement('div');
                alertDiv.className = 'alert alert-danger alert-dismissible fade show position-fixed';
                alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
                alertDiv.innerHTML = `
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong>Please fill in all required fields</strong>
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                `;
                document.body.appendChild(alertDiv);

                // Auto-remove after 5 seconds
                setTimeout(() => {
                    if (alertDiv.parentNode) {
                        alertDiv.remove();
                    }
                }, 5000);
            }
        });
    }

    // Add loading state to submit button
    if (form) {
        form.addEventListener('submit', function() {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !form.querySelector('.is-invalid')) {
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Creating Staff Member...';
                submitBtn.disabled = true;
            }
        });
    }

    // Enhanced form field interactions
    const allInputs = document.querySelectorAll('.form-control, .form-select');
    allInputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentNode.classList.add('focused');
        });

        input.addEventListener('blur', function() {
            this.parentNode.classList.remove('focused');
            if (this.value) {
                this.classList.add('has-value');
            } else {
                this.classList.remove('has-value');
            }
        });
    });
});
