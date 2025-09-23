/*
 * ZAIN HMS - Public Pages Core JavaScript
 * Alpine.js initialization and global stores
 * Version: 2.0 - Modular, organized
 */

// ===== Initialize Alpine.js Data Components (robust) =====
function registerAlpinePublicComponents() {
    if (!window.Alpine) return;

    // Global Alpine.js stores
    try {
        if (!Alpine.store('notifications')) {
            Alpine.store('notifications', {
                items: [],
                add(notification) {
                    const id = Date.now();
                    this.items.push({
                        id,
                        ...notification,
                        timestamp: new Date()
                    });
                    // Auto-remove after 5 seconds
                    setTimeout(() => this.remove(id), 5000);
                },
                remove(id) {
                    this.items = this.items.filter(item => item.id !== id);
                }
            });
        }
    } catch (_) { /* no-op */ }

    // Authentication controller (login, 2FA)
    try {
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
    } catch (_) { /* no-op */ }

    // Landing page controller
    try {
        Alpine.data('landingController', () => ({
            stats: {
                patients: 0,
                doctors: 0,
                staff: 0,
                satisfaction: 0
            },
            countersAnimated: false,

            init() {
                this.initScrollEffects();
                this.initSmoothScrolling();
                this.initFAQAccordion();
            },

            initScrollEffects() {
                const observerOptions = {
                    threshold: 0.1,
                    rootMargin: '0px 0px -50px 0px'
                };

                const observer = new IntersectionObserver((entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            entry.target.classList.add('fade-in');
                            if (entry.target.classList.contains('stats-section') && !this.countersAnimated) {
                                this.animateCounters();
                                this.countersAnimated = true;
                            }
                        }
                    });
                }, observerOptions);

                document.querySelectorAll('.feature-card, .stat-item, .stats-section').forEach(el => {
                    observer.observe(el);
                });
            },

            initSmoothScrolling() {
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
            },

            initFAQAccordion() {
                const items = document.querySelectorAll('.faq-item');
                items.forEach((item, index) => {
                    const btn = item.querySelector('.faq-question');
                    const panel = item.querySelector('.faq-answer');
                    if (!btn || !panel) return;

                    // Prevent duplicate binding
                    if (btn.dataset.bound === '1') return;
                    btn.dataset.bound = '1';

                    // ARIA attributes and relationships
                    const panelId = panel.id || `faq-panel-${index}`;
                    if (!panel.id) panel.id = panelId;
                    btn.setAttribute('type', 'button');
                    btn.setAttribute('aria-controls', panelId);
                    btn.setAttribute('aria-expanded', panel.classList.contains('show') ? 'true' : 'false');

                    const toggle = () => {
                        const isOpen = panel.classList.contains('show');
                        // If you want accordion behavior (one open at a time), uncomment the block below
                        // document.querySelectorAll('.faq-answer.show').forEach(openPanel => {
                        //     if (openPanel !== panel) {
                        //         openPanel.classList.remove('show');
                        //         const q = openPanel.closest('.faq-item')?.querySelector('.faq-question');
                        //         if (q) q.setAttribute('aria-expanded', 'false');
                        //     }
                        // });

                        if (isOpen) {
                            panel.classList.remove('show');
                            btn.setAttribute('aria-expanded', 'false');
                        } else {
                            panel.classList.add('show');
                            btn.setAttribute('aria-expanded', 'true');
                        }
                    };

                    btn.addEventListener('click', toggle);
                    btn.addEventListener('keydown', (e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            toggle();
                        }
                    });
                });
            },

            animateCounters() {
                const targets = { patients: 5000, doctors: 150, staff: 500, satisfaction: 98 };
                Object.keys(targets).forEach(key => {
                    this.animateCounter(key, targets[key]);
                });
            },

            animateCounter(key, target) {
                const duration = 2000;
                const start = Date.now();
                const update = () => {
                    const progress = Math.min((Date.now() - start) / duration, 1);
                    this.stats[key] = Math.floor(target * progress);
                    if (progress < 1) {
                        requestAnimationFrame(update);
                    }
                };
                update();
            },

            handleNewsletterSubmit(email) {
                // HTMX will handle the actual submission
                Alpine.store('notifications').add({
                    message: 'Thank you for subscribing! We\'ll keep you updated.',
                    type: 'success'
                });
            }
        }));
    } catch (_) { /* no-op */ }
}

// Register on alpine:init, and also try immediate registration if Alpine is already present
document.addEventListener('alpine:init', registerAlpinePublicComponents);
if (window.Alpine) {
    try { registerAlpinePublicComponents(); } catch (_) {}
} else {
    // Fallback after DOM is ready
    document.addEventListener('DOMContentLoaded', () => {
        if (window.Alpine) {
            try { registerAlpinePublicComponents(); } catch (_) {}
        }
    });
}

// ===== Global Utilities =====
// Shared FAQ accordion initializer (idempotent)
function setupFAQAccordion() {
    const items = document.querySelectorAll('.faq-item');
    items.forEach((item, index) => {
        const btn = item.querySelector('.faq-question');
        const panel = item.querySelector('.faq-answer');
        if (!btn || !panel) return;

        // Prevent duplicate binding
        if (btn.dataset.bound === '1') return;
        btn.dataset.bound = '1';

        // ARIA attributes and relationships
        const panelId = panel.id || `faq-panel-${index}`;
        if (!panel.id) panel.id = panelId;
        btn.setAttribute('type', 'button');
        btn.setAttribute('aria-controls', panelId);
        btn.setAttribute('aria-expanded', panel.classList.contains('show') ? 'true' : 'false');

        const toggle = () => {
            const isOpen = panel.classList.contains('show');
            if (isOpen) {
                panel.classList.remove('show');
                btn.setAttribute('aria-expanded', 'false');
            } else {
                panel.classList.add('show');
                btn.setAttribute('aria-expanded', 'true');
            }
        };

        btn.addEventListener('click', toggle);
        btn.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                toggle();
            }
        });
    });
}

// Enhanced HTMX configurations
document.addEventListener('DOMContentLoaded', function() {
    // Configure HTMX
    if (typeof htmx !== 'undefined') {
        // Global HTMX event handlers
        htmx.on('htmx:beforeRequest', function(evt) {
            // Show loading state
            const target = evt.detail.target;
            if (target) {
                target.classList.add('loading');
            }
        });

        htmx.on('htmx:afterRequest', function(evt) {
            // Hide loading state
            const target = evt.detail.target;
            if (target) {
                target.classList.remove('loading');
            }
        });

        htmx.on('htmx:responseError', function(evt) {
            try {
                if (window.Alpine && Alpine.store) {
                    Alpine.store('notifications').add({
                        message: 'An error occurred. Please try again.',
                        type: 'error'
                    });
                }
            } catch (_) {
                console.warn('HTMX error occurred');
            }
        });
    }

    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Smooth scrolling for anchor links
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

    // Fallback: ensure FAQ accordion works even if Alpine hasn't initialized yet
    try { setupFAQAccordion(); } catch (_) {}
});

/*
 * ZAIN HMS - Authentication Controller
 * Alpine.js component for login and authentication forms
 * Version: 1.0 - Secure, user-friendly authentication
 */

// (Component registration moved into registerAlpinePublicComponents above)
