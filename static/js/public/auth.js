/*
 * ZAIN HMS - Authentication Controller
 * Alpine.js component for login and authentication forms
 * Version: 1.0 - Secure, user-friendly authentication
 */

// Authentication controller (login, 2FA)
Alpine.data('authController', () => ({
    isLoading: false,
    showPassword: false,
    biometricSupported: false,
    formData: {
        username: '',
        password: '',
        remember: false
    },

    init() {
        this.checkBiometricSupport();
        this.initFormValidation();
    },

    checkBiometricSupport() {
        this.biometricSupported = !!(window.PublicKeyCredential && navigator.credentials);
    },

    initFormValidation() {
        // Real-time form validation
        this.$watch('formData', () => {
            this.validateForm();
        });
    },

    validateForm() {
        const form = this.$refs.authForm;
        if (form) {
            const isValid = form.checkValidity();
            return isValid;
        }
        return false;
    },

    togglePassword() {
        this.showPassword = !this.showPassword;
    },

    async handleBiometricAuth() {
        if (!this.biometricSupported) {
            Alpine.store('notifications').add({
                message: 'Biometric authentication is not supported on this device.',
                type: 'warning'
            });
            return;
        }

        this.isLoading = true;

        try {
            // Mock biometric authentication
            await new Promise(resolve => setTimeout(resolve, 2000));

            Alpine.store('notifications').add({
                message: 'Biometric authentication successful! Redirecting...',
                type: 'success'
            });

            setTimeout(() => {
                window.location.href = '/dashboard/';
            }, 1500);

        } catch (error) {
            console.error('Biometric authentication failed:', error);
            Alpine.store('notifications').add({
                message: 'Biometric authentication failed. Please try again.',
                type: 'error'
            });
        } finally {
            this.isLoading = false;
        }
    },

    async handleFormSubmit() {
        if (!this.validateForm()) {
            Alpine.store('notifications').add({
                message: 'Please fill in all required fields.',
                type: 'error'
            });
            return;
        }

        this.isLoading = true;
        // HTMX will handle the actual form submission
    },

    async submitLogin(event) {
        event.preventDefault();
        await this.handleFormSubmit();

        // If validation passes, submit the form
        if (this.validateForm() && !this.isLoading) {
            const form = this.$refs.authForm;
            if (form) {
                form.submit();
            }
        }
    },

    handleFormError(error) {
        this.isLoading = false;
        Alpine.store('notifications').add({
            message: error.message || 'Authentication failed. Please try again.',
            type: 'error'
        });
    }
}));
