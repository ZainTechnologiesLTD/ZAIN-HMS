/*
 * ZAIN HMS - Landing Page Controller
 * Alpine.js component for landing page interactions
 * Version: 1.0 - Interactive, engaging features
 */

// Landing page controller
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
