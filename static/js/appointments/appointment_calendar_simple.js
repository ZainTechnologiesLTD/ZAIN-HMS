document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing calendar...');

    var calendarEl = document.getElementById('appointmentCalendar');

    if (!calendarEl) {
        console.error('Calendar element not found!');
        return;
    }

    if (typeof FullCalendar === 'undefined') {
        console.error('FullCalendar library not loaded!');
        calendarEl.innerHTML = '<div class="alert alert-danger">Calendar library failed to load. Please refresh the page.</div>';
        return;
    }

    var calendar = new FullCalendar.Calendar(calendarEl, {
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
            extraParams: function() {
                return {
                    status: 'all',
                    priority: 'all',
                    doctor: 'all'
                };
            },
            failure: function() {
                console.error('Failed to load events');
                alert('Failed to load calendar events');
            }
        },
        loading: function(isLoading) {
            console.log('Loading:', isLoading);
        },
        eventDidMount: function(info) {
            console.log('Event mounted:', info.event);
        }
    });

    console.log('Rendering calendar...');
    calendar.render();
    console.log('Calendar initialized successfully');
});
