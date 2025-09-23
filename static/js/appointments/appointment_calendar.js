let calendar;

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded - Initializing calendar...');

    // Check if FullCalendar is loaded
    if (typeof FullCalendar === 'undefined') {
        console.error('FullCalendar is not loaded!');
        document.getElementById('appointmentCalendar').innerHTML = '<div class="alert alert-danger">Error: FullCalendar library failed to load. Please refresh the page.</div>';
        return;
    }

    const calendarEl = document.getElementById('appointmentCalendar');

    if (!calendarEl) {
        console.error('Calendar element with ID "appointmentCalendar" not found!');
        return;
    }

    console.log('Initializing FullCalendar...');

    try {
        calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay'
            },
            buttonText: {
                today: 'Today',
                month: 'Month',
                week: 'Week',
                day: 'Day'
            },
            height: 'auto',
            events: {
                url: '/en/appointments/calendar/events/',
                method: 'GET',
                extraParams: {
                    status: 'all',
                    priority: 'all',
                    doctor: 'all'
                },
                failure: function(error) {
                    console.error('Failed to load events:', error);
                    alert('Failed to load calendar events');
                }
            },
            loading: function(isLoading) {
                console.log('Loading events:', isLoading);
            },
            eventDidMount: function(info) {
                console.log('Event mounted:', info.event.title);
                // Add tooltip
                const title = info.event.title || 'Appointment';
                const time = info.event.start ? info.event.start.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : '';
                const status = info.event.extendedProps?.status || 'scheduled';
                info.el.title = `${title}\nTime: ${time}\nStatus: ${status}`;
            },
            eventClick: function(info) {
                console.log('Event clicked:', info.event);
                alert(`Appointment: ${info.event.title}`);
            },
            dateClick: function(info) {
                const url = `/en/appointments/create/?date=${info.dateStr}`;
                window.location.href = url;
            }
        });

        console.log('Rendering calendar...');
        calendar.render();
        console.log('Calendar initialized successfully!');

    } catch (error) {
        console.error('Error initializing calendar:', error);
        document.getElementById('appointmentCalendar').innerHTML = '<div class="alert alert-danger">Error initializing calendar: ' + error.message + '</div>';
    }

    // Setup view buttons
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            calendar.changeView(this.dataset.view);
        });
    });

    // Setup other event listeners
    setupOtherEventListeners();
});

function setupOtherEventListeners() {
    // Filter dropdown toggle
    const filterBtn = document.querySelector('.filter-btn');
    const filterMenu = document.getElementById('filterMenu');

    if (filterBtn && filterMenu) {
        filterBtn.addEventListener('click', function() {
            filterMenu.classList.toggle('show');
        });

        // Close filter menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.filter-dropdown')) {
                filterMenu.classList.remove('show');
            }
        });
    }
}

function refreshCalendar() {
    if (calendar) {
        calendar.refetchEvents();
        console.log('Calendar refreshed');
    }
}

function goToToday() {
    if (calendar) {
        calendar.today();
    }
}
