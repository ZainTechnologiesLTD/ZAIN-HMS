document.addEventListener('DOMContentLoaded', function() {
    const createAccountCheckbox = document.getElementById('id_create_user_account');
    const passwordFields = document.getElementById('password-fields');
    const firstNameField = document.getElementById('id_first_name');
    const lastNameField = document.getElementById('id_last_name');
    const usernameField = document.getElementById('id_username');
    const suggestionDiv = document.getElementById('username-suggestions');
    const suggestionList = document.getElementById('suggestion-list');

    function togglePasswordFields() {
        if (createAccountCheckbox && createAccountCheckbox.checked) {
            passwordFields.style.display = 'block';
        } else {
            passwordFields.style.display = 'none';
        }
    }

    function generateUsernameSuggestions() {
        const firstName = firstNameField ? firstNameField.value.toLowerCase().trim() : '';
        const lastName = lastNameField ? lastNameField.value.toLowerCase().trim() : '';

        if (firstName && lastName) {
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

            // Remove duplicates and current username value
            const currentUsername = usernameField ? usernameField.value.toLowerCase() : '';
            const uniqueSuggestions = [...new Set(suggestions)]
                .filter(s => s !== currentUsername)
                .slice(0, 6);

            if (uniqueSuggestions.length > 0) {
                suggestionList.innerHTML = uniqueSuggestions.map(s =>
                    `<span class="badge bg-light text-dark me-1 username-suggestion" style="cursor: pointer;">${s}</span>`
                ).join('');
                suggestionDiv.style.display = 'block';
            } else {
                suggestionDiv.style.display = 'none';
            }
        } else {
            suggestionDiv.style.display = 'none';
        }
    }

    // Event listeners
    if (createAccountCheckbox) {
        createAccountCheckbox.addEventListener('change', togglePasswordFields);
        togglePasswordFields(); // Initial state
    }

    if (firstNameField && lastNameField) {
        firstNameField.addEventListener('input', generateUsernameSuggestions);
        lastNameField.addEventListener('input', generateUsernameSuggestions);
        firstNameField.addEventListener('blur', generateUsernameSuggestions);
        lastNameField.addEventListener('blur', generateUsernameSuggestions);
    }

    // Click on suggestions to fill username field
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('username-suggestion')) {
            if (usernameField) {
                usernameField.value = e.target.textContent;
                suggestionDiv.style.display = 'none';
                // Trigger change event for any validation
                usernameField.dispatchEvent(new Event('change'));
            }
        }
    });

    // Hide suggestions when username field is focused
    if (usernameField) {
        usernameField.addEventListener('focus', function() {
            suggestionDiv.style.display = 'none';
        });
    }
});
