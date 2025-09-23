// Consolidated Patient Detail JavaScript
// Includes all functionality for patient detail pages

document.addEventListener('DOMContentLoaded', function() {
    const patientName = document.querySelector('.patient-name, h1')?.textContent?.trim() || 'Unknown Patient';
    console.log('Patient detail page loaded for:', patientName);

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[title]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers if any
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Tab navigation for patient details
    const tabButtons = document.querySelectorAll('.nav-tabs .nav-link');
    tabButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const targetTab = this.getAttribute('data-bs-target') || this.getAttribute('href');

            // Remove active class from all tabs
            tabButtons.forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('show', 'active'));

            // Add active class to clicked tab
            this.classList.add('active');
            const targetPane = document.querySelector(targetTab);
            if (targetPane) {
                targetPane.classList.add('show', 'active');
            }
        });
    });

    // Print functionality
    const printButtons = document.querySelectorAll('.btn-print, [data-action="print"]');
    printButtons.forEach(button => {
        button.addEventListener('click', function() {
            window.print();
        });
    });

    // Edit buttons
    const editButtons = document.querySelectorAll('.btn-edit, [data-action="edit"]');
    editButtons.forEach(button => {
        button.addEventListener('click', function() {
            const patientId = this.getAttribute('data-patient-id') || document.querySelector('[data-patient-id]')?.getAttribute('data-patient-id');
            if (patientId) {
                window.location.href = `/en/patients/${patientId}/edit/`;
            }
        });
    });

    // Delete button (soft delete)
    const deleteButton = document.querySelector('.btn-delete, [data-action="delete"]');
    if (deleteButton) {
        deleteButton.addEventListener('click', function() {
            const patientId = this.getAttribute('data-patient-id') || document.querySelector('[data-patient-id]')?.getAttribute('data-patient-id');
            if (patientId && confirm('Are you sure you want to deactivate this patient? This will hide them from active lists but preserve all medical records.')) {
                window.location.href = `/en/patients/${patientId}/delete/`;
            }
        });
    }

    // Vital signs chart initialization (if Chart.js is available)
    if (typeof Chart !== 'undefined') {
        initializeVitalsChart();
    }

    // Medical history accordion
    const accordionButtons = document.querySelectorAll('.accordion-button');
    accordionButtons.forEach(button => {
        button.addEventListener('click', function() {
            const target = document.querySelector(this.getAttribute('data-bs-target'));
            if (target) {
                const isExpanded = this.getAttribute('aria-expanded') === 'true';
                this.setAttribute('aria-expanded', !isExpanded);
                target.classList.toggle('show');
            }
        });
    });

    // Copy to clipboard functionality
    const copyButtons = document.querySelectorAll('[data-action="copy"]');
    copyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const textToCopy = this.getAttribute('data-text') || this.textContent;
            navigator.clipboard.writeText(textToCopy).then(() => {
                // Show temporary success feedback
                const originalText = this.innerHTML;
                this.innerHTML = '<i class="fas fa-check"></i> Copied!';
                this.classList.add('btn-success');
                setTimeout(() => {
                    this.innerHTML = originalText;
                    this.classList.remove('btn-success');
                }, 2000);
            });
        });
    });

    // Emergency contact quick dial
    const dialButtons = document.querySelectorAll('[data-action="dial"]');
    dialButtons.forEach(button => {
        button.addEventListener('click', function() {
            const phone = this.getAttribute('data-phone');
            if (phone) {
                window.location.href = `tel:${phone}`;
            }
        });
    });

    // Appointment booking
    const bookAppointmentBtn = document.querySelector('.btn-book-appointment, [data-action="book-appointment"]');
    if (bookAppointmentBtn) {
        bookAppointmentBtn.addEventListener('click', function() {
            const patientId = this.getAttribute('data-patient-id') || document.querySelector('[data-patient-id]')?.getAttribute('data-patient-id');
            if (patientId) {
                window.location.href = `/en/appointments/create/?patient=${patientId}`;
            }
        });
    }

    // Medical note quick add
    const addNoteBtn = document.querySelector('.btn-add-note, [data-action="add-note"]');
    if (addNoteBtn) {
        addNoteBtn.addEventListener('click', function() {
            const modal = new bootstrap.Modal(document.getElementById('addNoteModal'));
            modal.show();
        });
    }

    // Vital signs quick add
    const addVitalsBtn = document.querySelector('.btn-add-vitals, [data-action="add-vitals"]');
    if (addVitalsBtn) {
        addVitalsBtn.addEventListener('click', function() {
            const modal = new bootstrap.Modal(document.getElementById('addVitalsModal'));
            modal.show();
        });
    }
});

// Initialize vital signs chart
function initializeVitalsChart() {
    const chartCanvas = document.getElementById('vitalsChart');
    if (!chartCanvas) return;

    // Sample data - replace with actual patient data
    const ctx = chartCanvas.getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            datasets: [{
                label: 'Blood Pressure (Systolic)',
                data: [120, 118, 122, 119, 121, 117],
                borderColor: 'rgb(255, 99, 132)',
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
            }, {
                label: 'Blood Pressure (Diastolic)',
                data: [80, 78, 82, 79, 81, 77],
                borderColor: 'rgb(54, 162, 235)',
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: false
                }
            }
        }
    });
}

// Utility functions
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : 'success'} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}
