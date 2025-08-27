/**
 * Enhanced JavaScript for ZAIN HMS
 * Modern healthcare management system functionality
 */

class ZainHMS {
    constructor() {
        this.initializeEventListeners();
        this.initializeTooltips();
        this.initializeModals();
        this.initializeNotifications();
        this.initializeDarkMode();
        this.initializeFormValidation();
        this.initializeTableSorting();
        this.initializeSearchFilters();
        this.initializeRealTimeUpdates();
    }

    // Initialize event listeners
    initializeEventListeners() {
        document.addEventListener('DOMContentLoaded', () => {
            this.setupMobileMenu();
            this.setupSidebarToggle();
            this.setupQuickActions();
            this.setupAutoSave();
        });
    }

    // Enhanced mobile menu functionality
    setupMobileMenu() {
        const mobileMenuToggle = document.querySelector('[data-mobile-menu-toggle]');
        const mobileMenu = document.querySelector('[data-mobile-menu]');
        
        if (mobileMenuToggle && mobileMenu) {
            mobileMenuToggle.addEventListener('click', () => {
                mobileMenu.classList.toggle('show');
                document.body.classList.toggle('mobile-menu-open');
            });
        }
    }

    // Enhanced sidebar toggle functionality
    setupSidebarToggle() {
        const sidebarToggle = document.querySelector('[data-sidebar-toggle]');
        const sidebar = document.querySelector('.sidebar');
        const mainContent = document.querySelector('.main-content');
        
        if (sidebarToggle && sidebar) {
            sidebarToggle.addEventListener('click', () => {
                sidebar.classList.toggle('collapsed');
                mainContent?.classList.toggle('sidebar-collapsed');
                localStorage.setItem('sidebar-collapsed', sidebar.classList.contains('collapsed'));
            });

            // Restore sidebar state
            const sidebarCollapsed = localStorage.getItem('sidebar-collapsed') === 'true';
            if (sidebarCollapsed) {
                sidebar.classList.add('collapsed');
                mainContent?.classList.add('sidebar-collapsed');
            }
        }
    }

    // Quick actions functionality
    setupQuickActions() {
        const quickActionButtons = document.querySelectorAll('[data-quick-action]');
        
        quickActionButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const action = button.dataset.quickAction;
                this.handleQuickAction(action);
            });
        });
    }

    handleQuickAction(action) {
        const actions = {
            'new-patient': () => this.openModal('newPatientModal'),
            'new-appointment': () => this.openModal('newAppointmentModal'),
            'emergency-alert': () => this.triggerEmergencyAlert(),
            'view-schedule': () => this.openScheduleView(),
            'print-report': () => window.print()
        };

        if (actions[action]) {
            actions[action]();
        }
    }

    // Enhanced tooltip initialization
    initializeTooltips() {
        if (typeof bootstrap !== 'undefined') {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
        }
    }

    // Enhanced modal functionality
    initializeModals() {
        const modals = document.querySelectorAll('.modal');
        
        modals.forEach(modal => {
            modal.addEventListener('show.bs.modal', (e) => {
                this.onModalShow(e.target);
            });
            
            modal.addEventListener('hidden.bs.modal', (e) => {
                this.onModalHide(e.target);
            });
        });
    }

    onModalShow(modal) {
        // Auto-focus first input
        const firstInput = modal.querySelector('input, select, textarea');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }

        // Initialize form validation for modal forms
        const form = modal.querySelector('form');
        if (form) {
            this.initializeFormValidationForElement(form);
        }
    }

    onModalHide(modal) {
        // Clear form data if needed
        const form = modal.querySelector('form');
        if (form && form.dataset.clearOnHide === 'true') {
            form.reset();
            this.clearFormValidation(form);
        }
    }

    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal && typeof bootstrap !== 'undefined') {
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
        }
    }

    // Enhanced notification system
    initializeNotifications() {
        this.loadNotifications();
        this.setupNotificationRefresh();
        this.initializeToastContainer();
    }

    async loadNotifications() {
        try {
            const response = await fetch('/api/notifications/unread_count/');
            const data = await response.json();
            this.updateNotificationBadge(data.unread_count);
        } catch (error) {
            console.warn('Failed to load notifications:', error);
        }
    }

    updateNotificationBadge(count) {
        const badge = document.querySelector('.notification-badge');
        if (badge) {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline' : 'none';
        }
    }

    setupNotificationRefresh() {
        // Refresh notifications every 30 seconds
        setInterval(() => {
            this.loadNotifications();
        }, 30000);
    }

    initializeToastContainer() {
        if (!document.querySelector('.toast-container-enhanced')) {
            const container = document.createElement('div');
            container.className = 'toast-container-enhanced';
            document.body.appendChild(container);
        }
    }

    showToast(message, type = 'info', duration = 5000) {
        const container = document.querySelector('.toast-container-enhanced');
        const toast = document.createElement('div');
        toast.className = `toast-enhanced toast-${type}`;
        
        toast.innerHTML = `
            <div class="toast-content">
                <div class="toast-icon">
                    <i class="bi bi-${this.getToastIcon(type)}"></i>
                </div>
                <div class="toast-message">${message}</div>
                <button class="toast-close" onclick="this.parentElement.parentElement.remove()">
                    <i class="bi bi-x"></i>
                </button>
            </div>
        `;

        container.appendChild(toast);

        // Auto-remove after duration
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, duration);
    }

    getToastIcon(type) {
        const icons = {
            'success': 'check-circle',
            'error': 'exclamation-circle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    // Dark mode functionality
    initializeDarkMode() {
        const darkModeToggle = document.querySelector('[data-dark-mode-toggle]');
        const savedTheme = localStorage.getItem('theme');
        
        if (savedTheme) {
            this.setTheme(savedTheme);
        }

        if (darkModeToggle) {
            darkModeToggle.addEventListener('click', () => {
                const currentTheme = document.documentElement.dataset.theme;
                const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
                this.setTheme(newTheme);
            });
        }
    }

    setTheme(theme) {
        document.documentElement.dataset.theme = theme;
        localStorage.setItem('theme', theme);
        
        const darkModeToggle = document.querySelector('[data-dark-mode-toggle] i');
        if (darkModeToggle) {
            darkModeToggle.className = theme === 'dark' ? 'bi bi-sun' : 'bi bi-moon';
        }
    }

    // Enhanced form validation
    initializeFormValidation() {
        const forms = document.querySelectorAll('form[data-validate="true"]');
        forms.forEach(form => this.initializeFormValidationForElement(form));
    }

    initializeFormValidationForElement(form) {
        const inputs = form.querySelectorAll('input, select, textarea');
        
        inputs.forEach(input => {
            input.addEventListener('blur', () => this.validateInput(input));
            input.addEventListener('input', () => this.clearInputError(input));
        });

        form.addEventListener('submit', (e) => {
            if (!this.validateForm(form)) {
                e.preventDefault();
                e.stopPropagation();
            }
        });
    }

    validateInput(input) {
        const value = input.value.trim();
        const rules = this.getValidationRules(input);
        let isValid = true;
        let errorMessage = '';

        for (const rule of rules) {
            if (!rule.test(value)) {
                isValid = false;
                errorMessage = rule.message;
                break;
            }
        }

        this.showInputValidation(input, isValid, errorMessage);
        return isValid;
    }

    getValidationRules(input) {
        const rules = [];
        
        if (input.required) {
            rules.push({
                test: (value) => value.length > 0,
                message: 'This field is required'
            });
        }

        if (input.type === 'email') {
            rules.push({
                test: (value) => !value || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
                message: 'Please enter a valid email address'
            });
        }

        if (input.type === 'tel') {
            rules.push({
                test: (value) => !value || /^\+?[\d\s\-\(\)]+$/.test(value),
                message: 'Please enter a valid phone number'
            });
        }

        if (input.minLength) {
            rules.push({
                test: (value) => !value || value.length >= input.minLength,
                message: `Minimum ${input.minLength} characters required`
            });
        }

        return rules;
    }

    showInputValidation(input, isValid, message) {
        const feedbackElement = input.parentElement.querySelector('.invalid-feedback') || 
                               this.createFeedbackElement(input);
        
        input.classList.toggle('is-invalid', !isValid);
        input.classList.toggle('is-valid', isValid && input.value.trim());
        
        if (!isValid && message) {
            feedbackElement.textContent = message;
            feedbackElement.style.display = 'block';
        } else {
            feedbackElement.style.display = 'none';
        }
    }

    createFeedbackElement(input) {
        const feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        input.parentElement.appendChild(feedback);
        return feedback;
    }

    clearInputError(input) {
        input.classList.remove('is-invalid');
        const feedback = input.parentElement.querySelector('.invalid-feedback');
        if (feedback) {
            feedback.style.display = 'none';
        }
    }

    validateForm(form) {
        const inputs = form.querySelectorAll('input, select, textarea');
        let isFormValid = true;

        inputs.forEach(input => {
            if (!this.validateInput(input)) {
                isFormValid = false;
            }
        });

        return isFormValid;
    }

    clearFormValidation(form) {
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.classList.remove('is-invalid', 'is-valid');
        });

        const feedbacks = form.querySelectorAll('.invalid-feedback');
        feedbacks.forEach(feedback => {
            feedback.style.display = 'none';
        });
    }

    // Enhanced table sorting
    initializeTableSorting() {
        const sortableTables = document.querySelectorAll('table[data-sortable="true"]');
        
        sortableTables.forEach(table => {
            const headers = table.querySelectorAll('th[data-sortable]');
            
            headers.forEach(header => {
                header.style.cursor = 'pointer';
                header.innerHTML += ' <i class="bi bi-arrow-down-up text-muted"></i>';
                
                header.addEventListener('click', () => {
                    this.sortTable(table, header);
                });
            });
        });
    }

    sortTable(table, header) {
        const columnIndex = Array.from(header.parentElement.children).indexOf(header);
        const isNumeric = header.dataset.type === 'number';
        const isDate = header.dataset.type === 'date';
        const isAscending = !header.classList.contains('sort-asc');
        
        // Clear previous sort indicators
        table.querySelectorAll('th').forEach(th => {
            th.classList.remove('sort-asc', 'sort-desc');
            const icon = th.querySelector('i');
            if (icon) {
                icon.className = 'bi bi-arrow-down-up text-muted';
            }
        });

        // Set new sort indicator
        header.classList.add(isAscending ? 'sort-asc' : 'sort-desc');
        const icon = header.querySelector('i');
        if (icon) {
            icon.className = `bi bi-arrow-${isAscending ? 'up' : 'down'} text-primary`;
        }

        // Sort table rows
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.rows);
        
        rows.sort((a, b) => {
            const aValue = a.cells[columnIndex].textContent.trim();
            const bValue = b.cells[columnIndex].textContent.trim();
            
            let comparison = 0;
            
            if (isNumeric) {
                comparison = parseFloat(aValue) - parseFloat(bValue);
            } else if (isDate) {
                comparison = new Date(aValue) - new Date(bValue);
            } else {
                comparison = aValue.localeCompare(bValue);
            }
            
            return isAscending ? comparison : -comparison;
        });

        // Reorder rows
        rows.forEach(row => tbody.appendChild(row));
    }

    // Enhanced search and filters
    initializeSearchFilters() {
        const searchInputs = document.querySelectorAll('[data-search-target]');
        
        searchInputs.forEach(input => {
            let searchTimeout;
            
            input.addEventListener('input', () => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.performSearch(input);
                }, 300);
            });
        });

        const filterSelects = document.querySelectorAll('[data-filter-target]');
        filterSelects.forEach(select => {
            select.addEventListener('change', () => {
                this.performFilter(select);
            });
        });
    }

    performSearch(input) {
        const target = document.querySelector(input.dataset.searchTarget);
        const searchTerm = input.value.toLowerCase();
        
        if (target) {
            const rows = target.querySelectorAll('tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                const matches = text.includes(searchTerm);
                row.style.display = matches ? '' : 'none';
            });
        }
    }

    performFilter(select) {
        const target = document.querySelector(select.dataset.filterTarget);
        const filterValue = select.value;
        const filterColumn = select.dataset.filterColumn;
        
        if (target && filterColumn) {
            const rows = target.querySelectorAll('tbody tr');
            
            rows.forEach(row => {
                const cell = row.querySelector(`td:nth-child(${filterColumn})`);
                if (cell) {
                    const cellValue = cell.textContent.trim();
                    const matches = !filterValue || cellValue === filterValue;
                    row.style.display = matches ? '' : 'none';
                }
            });
        }
    }

    // Auto-save functionality
    setupAutoSave() {
        const autoSaveForms = document.querySelectorAll('form[data-auto-save="true"]');
        
        autoSaveForms.forEach(form => {
            const inputs = form.querySelectorAll('input, select, textarea');
            
            inputs.forEach(input => {
                input.addEventListener('input', this.debounce(() => {
                    this.autoSaveForm(form);
                }, 2000));
            });
        });
    }

    async autoSaveForm(form) {
        try {
            const formData = new FormData(form);
            const response = await fetch(form.action + '?auto_save=true', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCsrfToken()
                }
            });

            if (response.ok) {
                this.showAutoSaveIndicator(true);
            } else {
                this.showAutoSaveIndicator(false);
            }
        } catch (error) {
            console.warn('Auto-save failed:', error);
            this.showAutoSaveIndicator(false);
        }
    }

    showAutoSaveIndicator(success) {
        const indicator = document.querySelector('.auto-save-indicator') || 
                         this.createAutoSaveIndicator();
        
        indicator.className = `auto-save-indicator ${success ? 'success' : 'error'}`;
        indicator.textContent = success ? 'Auto-saved' : 'Auto-save failed';
        indicator.style.display = 'block';

        setTimeout(() => {
            indicator.style.display = 'none';
        }, 2000);
    }

    createAutoSaveIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'auto-save-indicator';
        indicator.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 14px;
            font-weight: 500;
            z-index: 9999;
            display: none;
        `;
        document.body.appendChild(indicator);
        return indicator;
    }

    // Real-time updates
    initializeRealTimeUpdates() {
        if (window.WebSocket) {
            this.setupWebSocketConnection();
        } else {
            this.setupPollingUpdates();
        }
    }

    setupWebSocketConnection() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/updates/`;
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleRealTimeUpdate(data);
            };
            
            this.ws.onclose = () => {
                // Reconnect after 5 seconds
                setTimeout(() => this.setupWebSocketConnection(), 5000);
            };
        } catch (error) {
            console.warn('WebSocket connection failed, falling back to polling');
            this.setupPollingUpdates();
        }
    }

    setupPollingUpdates() {
        setInterval(() => {
            this.fetchUpdates();
        }, 10000); // Poll every 10 seconds
    }

    async fetchUpdates() {
        try {
            const response = await fetch('/api/updates/');
            const data = await response.json();
            data.updates.forEach(update => this.handleRealTimeUpdate(update));
        } catch (error) {
            console.warn('Failed to fetch updates:', error);
        }
    }

    handleRealTimeUpdate(data) {
        switch (data.type) {
            case 'notification':
                this.showToast(data.message, 'info');
                this.loadNotifications();
                break;
            case 'emergency':
                this.showToast(data.message, 'error', 10000);
                this.triggerEmergencyAlert();
                break;
            case 'appointment':
                this.updateAppointmentStatus(data);
                break;
            case 'patient_update':
                this.updatePatientInfo(data);
                break;
        }
    }

    // Utility functions
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }

    // Emergency alert functionality
    triggerEmergencyAlert() {
        const alertModal = document.getElementById('emergencyAlertModal');
        if (alertModal) {
            const modal = new bootstrap.Modal(alertModal);
            modal.show();
        }
    }

    // Schedule view functionality
    openScheduleView() {
        window.location.href = '/schedule/';
    }

    // Update functions for real-time data
    updateAppointmentStatus(data) {
        const appointmentElement = document.querySelector(`[data-appointment-id="${data.appointment_id}"]`);
        if (appointmentElement) {
            const statusElement = appointmentElement.querySelector('.appointment-status');
            if (statusElement) {
                statusElement.textContent = data.status;
                statusElement.className = `appointment-status status-${data.status.toLowerCase()}`;
            }
        }
    }

    updatePatientInfo(data) {
        const patientElement = document.querySelector(`[data-patient-id="${data.patient_id}"]`);
        if (patientElement) {
            // Update patient information as needed
            const nameElement = patientElement.querySelector('.patient-name');
            if (nameElement && data.name) {
                nameElement.textContent = data.name;
            }
        }
    }
}

// Initialize the HMS system when the DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.zainHMS = new ZainHMS();
});

// Global utility functions
window.showToast = (message, type, duration) => {
    if (window.zainHMS) {
        window.zainHMS.showToast(message, type, duration);
    }
};

window.openModal = (modalId) => {
    if (window.zainHMS) {
        window.zainHMS.openModal(modalId);
    }
};
