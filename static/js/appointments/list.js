    function appointmentManager() {
        return {
            currentView: 'grid',
            selectedAppointments: [],

            init() {
                this.setupEventListeners();
                this.initializeView();
            },

            setupEventListeners() {
                // View mode switching
                document.querySelectorAll('input[name="viewMode"]').forEach(input => {
                    input.addEventListener('change', (e) => {
                        this.switchView(e.target.id.replace('View', ''));
                    });
                });

                // Select all checkbox
                document.getElementById('selectAll').addEventListener('change', (e) => {
                    this.toggleSelectAll(e.target.checked);
                });
            },

            switchView(viewType) {
                // Hide all views
                document.querySelectorAll('.view-content').forEach(view => {
                    view.classList.add('d-none');
                });

                // Show selected view
                document.getElementById(viewType + 'ViewContent').classList.remove('d-none');
                this.currentView = viewType;

                if (viewType === 'calendar') {
                    this.initializeCalendar();
                }
            },

            initializeView() {
                // Default to grid view
                this.switchView('grid');
            },

            toggleSelectAll(checked) {
                document.querySelectorAll('.appointment-checkbox').forEach(checkbox => {
                    checkbox.checked = checked;
                });
                this.updateSelectedAppointments();
            },

            updateSelectedAppointments() {
                this.selectedAppointments = Array.from(
                    document.querySelectorAll('.appointment-checkbox:checked')
                ).map(checkbox => checkbox.value);
            },

            initializeCalendar() {
                // Initialize calendar view
                const calendarGrid = document.getElementById('calendarGrid');
                // Calendar implementation would go here
                console.log('Calendar view initialized');
            }
        }
    }

    function markCompleted(appointmentId) {
        if (confirm('Mark this appointment as completed?')) {
            fetch(`/appointments/complete/${appointmentId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json',
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification('Appointment marked as completed!', 'success');
                    location.reload();
                } else {
                    showNotification('Failed to update appointment', 'error');
                }
            });
        }
    }

    function cancelAppointment(appointmentId) {
        if (confirm('Are you sure you want to cancel this appointment?')) {
            fetch(`/appointments/cancel/${appointmentId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json',
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification('Appointment cancelled successfully!', 'success');
                    location.reload();
                } else {
                    showNotification('Failed to cancel appointment', 'error');
                }
            });
        }
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Communication functions moved to /static/js/communication.js

    // Real-time updates
    document.addEventListener('DOMContentLoaded', function() {
        // Refresh appointment data every 30 seconds
        setInterval(() => {
            htmx.trigger('#appointmentsList', 'refresh');
        }, 30000);
    });


    document.addEventListener('DOMContentLoaded', function() {
        // Initialize appointments functionality
        if (typeof initAppointments === 'function') {
            initAppointments();
        }
    });
