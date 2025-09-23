// Global date picker functionality
let datePickerInstances = {};

function initializeDateFields() {
    const dateFields = document.querySelectorAll('.date-input-field');

    dateFields.forEach(field => {
        const fieldId = field.id;

        // Initialize Flatpickr for this field
        if (!datePickerInstances[fieldId]) {
            datePickerInstances[fieldId] = flatpickr(field, {
                dateFormat: 'd/m/Y',
                allowInput: true,
                clickOpens: false, // We'll control opening via button
                onChange: function(selectedDates, dateStr, instance) {
                    if (dateStr) {
                        field.value = dateStr;
                        field.dispatchEvent(new Event('change'));
                    }
                }
            });
        }

        // Add input validation with debouncing
        let validationTimeout;
        field.addEventListener('input', function(e) {
            // Clear any existing timeout
            clearTimeout(validationTimeout);

            // Only validate if there's content or if field was previously invalid
            const hasContent = e.target.value.trim().length > 0;
            const wasInvalid = e.target.classList.contains('is-invalid');

            if (hasContent || wasInvalid) {
                // Debounce validation to avoid showing errors while typing
                validationTimeout = setTimeout(() => {
                    validateDateInput(e.target);
                }, 500); // Wait 500ms after user stops typing
            } else {
                // Clear validation immediately for empty fields
                validateDateInput(e.target);
            }
        });

        field.addEventListener('change', function(e) {
            clearTimeout(validationTimeout); // Cancel any pending validation
            validateDateInput(e.target);
            parseAndFormatDate(e.target);
        });

        field.addEventListener('blur', function(e) {
            clearTimeout(validationTimeout); // Cancel any pending validation
            validateDateInput(e.target);
        });
    });
}

function openDatePicker(fieldId) {
    if (datePickerInstances[fieldId]) {
        datePickerInstances[fieldId].open();
    }
}

function parseAndFormatDate(field) {
    const value = field.value.trim();
    if (!value) return;

    // Try to parse various date formats
    const patterns = [
        /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/, // DD/MM/YYYY
        /^(\d{1,2})-(\d{1,2})-(\d{4})$/, // DD-MM-YYYY
        /^(\d{1,2})\.(\d{1,2})\.(\d{4})$/, // DD.MM.YYYY
    ];

    for (const pattern of patterns) {
        const match = value.match(pattern);
        if (match) {
            const day = parseInt(match[1]);
            const month = parseInt(match[2]);
            const year = parseInt(match[3]);

            if (day >= 1 && day <= 31 && month >= 1 && month <= 12 && year >= 1900) {
                const formattedDate = `${String(day).padStart(2, '0')}/${String(month).padStart(2, '0')}/${year}`;
                if (field.value !== formattedDate) {
                    field.value = formattedDate;
                }
                return;
            }
        }
    }
}

function validateDateInput(field) {
    const value = field.value.trim();
    const fieldId = field.id;
    let validationElement = document.getElementById(fieldId + '-validation');

    if (!validationElement) {
        validationElement = document.createElement('div');
        validationElement.id = fieldId + '-validation';
        validationElement.className = 'validation-message';
        field.parentNode.appendChild(validationElement);
    }

    // Clear validation if field is empty - this is normal state
    if (!value) {
        hideValidation(fieldId + '-validation');
        field.classList.remove('is-valid', 'is-invalid');
        return true; // Empty is valid, let Django handle required field validation
    }

    // Simple age calculation for date of birth fields - no validation
    if (fieldId.includes('date_of_birth')) {
        const age = calculateAge(value);
        if (!isNaN(age) && age >= 0 && age <= 150) {
            showValidation(fieldId + '-validation', '✓ Age: ' + age + ' years old', 'success');
            field.classList.remove('is-invalid');
            field.classList.add('is-valid');
        } else {
            hideValidation(fieldId + '-validation');
            field.classList.remove('is-valid', 'is-invalid');
        }
    } else {
        // For non-birth date fields, just clear validation
        hideValidation(fieldId + '-validation');
        field.classList.remove('is-invalid');
        field.classList.add('is-valid');
    }

    return true;
}

function calculateAge(birthDate) {
    try {
        const today = new Date();
        let birth;

        if (typeof birthDate === 'string') {
            // Simple DD/MM/YYYY parsing
            const parts = birthDate.split('/');
            if (parts.length === 3) {
                const day = parseInt(parts[0]);
                const month = parseInt(parts[1]) - 1; // Month is 0-indexed
                const year = parseInt(parts[2]);
                birth = new Date(year, month, day);
            } else {
                return NaN;
            }
        } else if (birthDate instanceof Date) {
            birth = birthDate;
        } else {
            return NaN;
        }

        // Check if date is valid
        if (isNaN(birth.getTime())) {
            return NaN;
        }

        // Calculate age
        let age = today.getFullYear() - birth.getFullYear();
        const monthDiff = today.getMonth() - birth.getMonth();

        if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
            age--;
        }

        return age;
    } catch (error) {
        return NaN;
    }
}

function showValidation(elementId, message, type) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = message;
        element.className = `validation-message validation-${type}`;
        element.style.display = 'block';
    }
}

function hideValidation(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = 'none';
    }
}

function clearDate(fieldId) {
    const field = document.getElementById(fieldId);
    if (field) {
        field.value = '';
        field.dispatchEvent(new Event('change'));

        // Clear validation messages
        if (fieldId.includes('date_of_birth')) {
            hideValidation(fieldId + '-validation');
        }
        field.classList.remove('is-valid', 'is-invalid');
    }
}

// Quick date selection functions
function setQuickDate(fieldId, type, value) {
    const field = document.getElementById(fieldId);
    if (!field) return;

    const today = new Date();
    let targetDate = new Date();

    if (type === 'age') {
        targetDate.setFullYear(today.getFullYear() - value);
    } else if (type === 'past') {
        switch(value) {
            case 'today':
                targetDate = today;
                break;
            case '1-week':
                targetDate.setDate(today.getDate() - 7);
                break;
            case '1-month':
                targetDate.setMonth(today.getMonth() - 1);
                break;
            case '6-months':
                targetDate.setMonth(today.getMonth() - 6);
                break;
            case '1-year':
                targetDate.setFullYear(today.getFullYear() - 1);
                break;
        }
    }

    const day = String(targetDate.getDate()).padStart(2, '0');
    const month = String(targetDate.getMonth() + 1).padStart(2, '0');
    const year = targetDate.getFullYear();

    field.value = `${day}/${month}/${year}`;
    field.dispatchEvent(new Event('change'));

    // Add visual feedback
    field.style.borderColor = '#28a745';
    setTimeout(() => {
        field.style.borderColor = '';
    }, 1000);
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeDateFields();
});

// Re-initialize if new fields are added dynamically
function reinitializeDateFields() {
    initializeDateFields();
}
