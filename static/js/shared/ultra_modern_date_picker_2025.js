// Latest Modern Date System - 2025 Edition
// Ultra-simple, no-validation, always-working system
// Duplicate-safe: prevents re-initialization & duplicate calendar buttons

if (!window.__UltraModernDatePickerLoaded) {

class UltraModernDatePicker {
    constructor() {
        this.cleanupDuplicateButtons();
        this.initializeDatePickers();
    }

    cleanupDuplicateButtons() {
        // Remove any orphaned calendar buttons
        const allButtons = document.querySelectorAll('.ultra-modern-calendar-btn');
        const containers = document.querySelectorAll('.ultra-modern-date-container');

        // Keep only one button per container
        containers.forEach(container => {
            const buttons = container.querySelectorAll('.ultra-modern-calendar-btn');
            if (buttons.length > 1) {
                // Keep the first one, remove the rest
                for (let i = 1; i < buttons.length; i++) {
                    buttons[i].remove();
                }
            }
        });

        // Remove any buttons not in containers
        allButtons.forEach(button => {
            if (!button.closest('.ultra-modern-date-container')) {
                button.remove();
            }
        });
    }

    initializeDatePickers() {
        // Find all date input fields
        const dateFields = document.querySelectorAll('input[type="date"], input[data-enable-time], input.datetime-field, .date-input, .date-input-field, input[name*="date"], input[name*="datetime"], input[id*="date"]');

        dateFields.forEach(field => {
            this.setupModernDateField(field);
        });

        // Also setup any fields that get added dynamically
        this.setupDynamicFieldDetection();
    }

    setupModernDateField(field) {
        // Skip if already processed (multiple checks for safety)
        if (field.classList.contains('ultra-modern-processed')) return;
        if (field.__ultraModernDateProcessed) return;
        if (field.closest('.ultra-modern-date-container')) return; // Already in container

        // Mark as processed with multiple flags
        field.classList.add('ultra-modern-processed');
        field.__ultraModernDateProcessed = true;

        // Clean up any existing duplicate buttons first
        const existingContainers = field.parentNode.querySelectorAll('.ultra-modern-date-container');
        existingContainers.forEach(container => {
            if (container !== field.parentNode && !container.contains(field)) {
                const buttons = container.querySelectorAll('.ultra-modern-calendar-btn');
                buttons.forEach(btn => btn.remove());
            }
        });

        // Create modern container
        const container = document.createElement('div');
        container.className = 'ultra-modern-date-container';

        // Insert container before the field
        field.parentNode.insertBefore(container, field);

        // Move field into container
        container.appendChild(field);

        // Preserve original type then force text to avoid native browser validation popups
        try {
            if (!field.dataset.originalType) field.dataset.originalType = field.type;
            field.type = 'text';
        } catch(e) {}

        // Style the field (preserve existing classes like form-control)
        if (!field.classList.contains('ultra-modern-date-input')) {
            field.classList.add('ultra-modern-date-input');
        }

        // Determine if this should be a date-time picker
        const isDateTime = field.classList.contains('datetime-field') || field.dataset.enableTime === 'true' || field.name.includes('date_time') || field.name.includes('datetime');

        // Set placeholder
        field.placeholder = isDateTime ? 'DD/MM/YYYY HH:MM' : 'DD/MM/YYYY';

        // Create calendar button only if one not already present (triple check)
        let calendarBtn = container.querySelector('.ultra-modern-calendar-btn');
        if (!calendarBtn && !field.__calendarButtonCreated) {
            calendarBtn = document.createElement('button');
            calendarBtn.type = 'button';
            calendarBtn.className = 'ultra-modern-calendar-btn';
            calendarBtn.innerHTML = '<i class="fas fa-calendar-alt"></i>';
            container.appendChild(calendarBtn);
            field.__calendarButtonCreated = true;
        }

        // Create age display (for birth date fields)
        let ageDisplay = null;
        if (field.name && (field.name.includes('date_of_birth') || field.name.includes('birth') || field.id.includes('birth'))) {
            ageDisplay = document.createElement('div');
            ageDisplay.className = 'age-display hidden';
            container.appendChild(ageDisplay);
        }

        // Create quick date buttons for birth dates
        if (ageDisplay) {
            const quickButtons = document.createElement('div');
            quickButtons.className = 'quick-date-buttons';
            quickButtons.innerHTML = `
                <button type="button" class="quick-date-btn" data-years="20">20 years ago</button>
                <button type="button" class="quick-date-btn" data-years="30">30 years ago</button>
                <button type="button" class="quick-date-btn" data-years="40">40 years ago</button>
                <button type="button" class="quick-date-btn" data-years="50">50 years ago</button>
                <button type="button" class="quick-date-btn clear">Clear</button>
            `;
            container.appendChild(quickButtons);

            // Setup quick button events
            quickButtons.addEventListener('click', (e) => {
                if (e.target.classList.contains('quick-date-btn')) {
                    e.preventDefault();

                    if (e.target.classList.contains('clear')) {
                        field.value = '';
                        this.updateAgeDisplay(field, ageDisplay);
                    } else {
                        const years = parseInt(e.target.dataset.years);
                        const date = new Date();
                        date.setFullYear(date.getFullYear() - years);
                        const formattedDate = this.formatDateToDDMMYYYY(date);
                        field.value = formattedDate;
                        this.updateAgeDisplay(field, ageDisplay);
                    }
                }
            });
        }

        // Build flatpickr config
        const pickerConfig = {
            dateFormat: isDateTime ? 'd/m/Y H:i' : 'd/m/Y',
            allowInput: true,
            clickOpens: true, // allow direct input click
            enableTime: isDateTime,
            time_24hr: true,
            locale: { firstDayOfWeek: 1 },
            onChange: () => {
                try { field.dispatchEvent(new Event('change', { bubbles: true })); } catch(e) {}
                if (ageDisplay) {
                    this.updateAgeDisplay(field, ageDisplay);
                }
            }
        };

        // Initialize Flatpickr with latest settings
        const flatpickrInstance = flatpickr(field, pickerConfig);

        // Calendar button event
        calendarBtn.addEventListener('click', (e) => {
            e.preventDefault();
            flatpickrInstance.open();
        });

        // Focus opens picker (fallback if button hidden)
        field.addEventListener('focus', () => {
            if (flatpickrInstance) flatpickrInstance.open();
        });

        // Input event for real-time age calculation
        field.addEventListener('input', () => {
            if (ageDisplay) {
                this.updateAgeDisplay(field, ageDisplay);
            }
        });

        // Initial age calculation if field has value
        if (ageDisplay && field.value) {
            this.updateAgeDisplay(field, ageDisplay);
        }
    }

    formatDateToDDMMYYYY(date) {
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();
        return `${day}/${month}/${year}`;
    }

    calculateAge(dateString) {
        if (!dateString) return null;

        // Parse DD/MM/YYYY format
        const parts = dateString.split('/');
        if (parts.length !== 3) return null;

        const day = parseInt(parts[0], 10);
        const month = parseInt(parts[1], 10);
        const year = parseInt(parts[2], 10);

        // Validate date parts
        if (day < 1 || day > 31 || month < 1 || month > 12 || year < 1900) {
            return null;
        }

        const birthDate = new Date(year, month - 1, day);
        const today = new Date();

        // Check if constructed date matches input
        if (birthDate.getDate() !== day || birthDate.getMonth() !== (month - 1) || birthDate.getFullYear() !== year) {
            return null;
        }

        let age = today.getFullYear() - birthDate.getFullYear();
        const monthDiff = today.getMonth() - birthDate.getMonth();

        if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
            age--;
        }

        return age >= 0 ? age : null;
    }

    updateAgeDisplay(field, ageDisplay) {
        const age = this.calculateAge(field.value);

        if (age !== null) {
            ageDisplay.innerHTML = `
                <i class="fas fa-birthday-cake"></i>
                <strong>${age} years old</strong>
            `;
            ageDisplay.classList.remove('hidden');
        } else {
            ageDisplay.classList.add('hidden');
        }
    }

    setupDynamicFieldDetection() {
        // Watch for dynamically added date fields
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === 1) { // Element node
                        const dateFields = node.querySelectorAll ?
                            node.querySelectorAll('input[type="date"], .date-input, .date-input-field, input[name*="date"], input[id*="date"]') : [];

                        dateFields.forEach(field => {
                            if (!field.classList.contains('ultra-modern-processed')) {
                                this.setupModernDateField(field);
                            }
                        });
                    }
                });
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
}

// Initialize when DOM is ready (once)
document.addEventListener('DOMContentLoaded', () => {
    if (!window.__UltraModernDatePickerInitialized) {
        const instance = new UltraModernDatePicker();
        window.__UltraModernDatePickerInstance = instance;
        window.__UltraModernDatePickerInitialized = true;
    } else {
        // If already initialized, just clean up duplicates
        if (window.__UltraModernDatePickerInstance) {
            window.__UltraModernDatePickerInstance.cleanupDuplicateButtons();
        }
    }
});

// Immediate init if script injected after DOMContentLoaded (e.g., HTMX/modal)
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    if (!window.__UltraModernDatePickerInitialized) {
        const instance = new UltraModernDatePicker();
        window.__UltraModernDatePickerInstance = instance;
        window.__UltraModernDatePickerInitialized = true;
    } else {
        // If already initialized, just clean up duplicates
        if (window.__UltraModernDatePickerInstance) {
            window.__UltraModernDatePickerInstance.cleanupDuplicateButtons();
        }
    }
}

// Additional failsafe - initialize after a short delay
setTimeout(() => {
    if (!window.__UltraModernDatePickerInitialized) {
        const instance = new UltraModernDatePicker();
        window.__UltraModernDatePickerInstance = instance;
        window.__UltraModernDatePickerInitialized = true;
    } else {
        // Force re-scan for any missed fields
        if (window.__UltraModernDatePickerInstance) {
            window.__UltraModernDatePickerInstance.initializeDatePickers();
        }
    }
}, 1000);

// Expose manual re-init helper
window.initializeUltraModernDatePickers = function() {
    if (window.__UltraModernDatePickerInitialized) {
        // Re-scan only (safe)
        try {
            if (window.__UltraModernDatePickerInstance) {
                window.__UltraModernDatePickerInstance.cleanupDuplicateButtons();
                window.__UltraModernDatePickerInstance.initializeDatePickers();
            }
        } catch(e) {}
    } else {
        const instance = new UltraModernDatePicker();
        window.__UltraModernDatePickerInstance = instance;
        window.__UltraModernDatePickerInitialized = true;
    }
};

// Expose duplicate cleanup function
window.cleanupDuplicateDateButtons = function() {
    if (window.__UltraModernDatePickerInstance) {
        window.__UltraModernDatePickerInstance.cleanupDuplicateButtons();
    } else {
        // Manual cleanup if no instance available
        const containers = document.querySelectorAll('.ultra-modern-date-container');
        containers.forEach(container => {
            const buttons = container.querySelectorAll('.ultra-modern-calendar-btn');
            if (buttons.length > 1) {
                for (let i = 1; i < buttons.length; i++) {
                    buttons[i].remove();
                }
            }
        });

        // Remove orphaned buttons
        const allButtons = document.querySelectorAll('.ultra-modern-calendar-btn');
        allButtons.forEach(button => {
            if (!button.closest('.ultra-modern-date-container')) {
                button.remove();
            }
        });
    }
};

window.__UltraModernDatePickerLoaded = true;
}
