// Alpine.js component for appointment management
function appointmentManager() {
    return {
        init() {
            console.log('Appointment manager initialized');
            // Initialize any required functionality
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // Initialize date pickers
    flatpickr("#dateFromFilter", {
        dateFormat: "Y-m-d",
        onChange: function() {
            updateFilterTags();
        }
    });

    flatpickr("#dateToFilter", {
        dateFormat: "Y-m-d",
        onChange: function() {
            updateFilterTags();
        }
    });

    // Real-time search
    let searchTimeout;
    document.getElementById('searchInput').addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            this.form.submit();
        }, 500);
    });

    // Filter change handlers
    document.querySelectorAll('#statusFilter, #priorityFilter, #doctorFilter').forEach(select => {
        select.addEventListener('change', function() {
            updateFilterTags();
            this.form.submit();
        });
    });

    // Initialize filter tags
    updateFilterTags();

    // Initialize calendar if needed
    if (document.getElementById('calendarView').style.display !== 'none') {
        initializeCalendar();
    }
});

function switchView(viewType) {
    const listView = document.getElementById('listView');
    const calendarView = document.getElementById('calendarView');
    const buttons = document.querySelectorAll('.view-toggle button');

    buttons.forEach(btn => btn.classList.remove('active'));

    if (viewType === 'list') {
        listView.style.display = 'block';
        calendarView.style.display = 'none';
        buttons[0].classList.add('active');
    } else {
        listView.style.display = 'none';
        calendarView.style.display = 'block';
        buttons[1].classList.add('active');
        initializeCalendar();
    }
}

function initializeCalendar() {
    const calendarEl = document.getElementById('appointmentCalendar');
    if (calendarEl && !calendarEl.hasChildNodes()) {
        const calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay'
            },
            events: function(fetchInfo, successCallback, failureCallback) {
                fetch(`/appointments/api/calendar/?start=${fetchInfo.startStr}&end=${fetchInfo.endStr}`)
                    .then(response => response.json())
                    .then(data => successCallback(data.events))
                    .catch(error => failureCallback(error));
            },
            eventClick: function(info) {
                window.location.href = `/appointments/${info.event.id}/`;
            },
            eventClassNames: function(arg) {
                return [`priority-${arg.event.extendedProps.priority}`, `status-${arg.event.extendedProps.status}`];
            }
        });
        calendar.render();
    }
}

function updateFilterTags() {
    const container = document.getElementById('filterTags');
    const tags = [];

    // Check each filter
    const search = document.getElementById('searchInput').value;
    const status = document.getElementById('statusFilter').value;
    const priority = document.getElementById('priorityFilter').value;
    const doctor = document.getElementById('doctorFilter').value;
    const dateFrom = document.getElementById('dateFromFilter').value;
    const dateTo = document.getElementById('dateToFilter').value;

    if (search) tags.push({label: `Search: ${search}`, field: 'search'});
    if (status) tags.push({label: `Status: ${status}`, field: 'status'});
    if (priority) tags.push({label: `Priority: ${priority}`, field: 'priority'});
    if (doctor) {
        const doctorText = document.querySelector(`#doctorFilter option[value="${doctor}"]`).textContent;
        tags.push({label: `Doctor: ${doctorText}`, field: 'doctor'});
    }
    if (dateFrom) tags.push({label: `From: ${dateFrom}`, field: 'date_from'});
    if (dateTo) tags.push({label: `To: ${dateTo}`, field: 'date_to'});

    container.innerHTML = tags.map(tag =>
        `<span class="filter-tag">
            ${tag.label}
            <span class="remove" onclick="removeFilter('${tag.field}')">&times;</span>
        </span>`
    ).join('');
}

function removeFilter(field) {
    const fieldMap = {
        'search': 'searchInput',
        'status': 'statusFilter',
        'priority': 'priorityFilter',
        'doctor': 'doctorFilter',
        'date_from': 'dateFromFilter',
        'date_to': 'dateToFilter'
    };

    const element = document.getElementById(fieldMap[field]);
    if (element) {
        element.value = '';
        updateFilterTags();
        element.form.submit();
    }
}

function clearFilters() {
    document.getElementById('filterForm').reset();
    updateFilterTags();
    window.location.href = window.location.pathname;
}

function cancelAppointment(appointmentId) {
    document.getElementById('appointmentIdToCancel').value = appointmentId;
    const modal = new bootstrap.Modal(document.getElementById('cancelModal'));
    modal.show();
}

function confirmCancelAppointment() {
    const appointmentId = document.getElementById('appointmentIdToCancel').value;
    const reason = document.getElementById('cancellationReason').value;

    if (!reason.trim()) {
        alert('Please provide a reason for cancellation.');
        return;
    }

    fetch(`/appointments/${appointmentId}/cancel/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({
            cancellation_reason: reason
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            bootstrap.Modal.getInstance(document.getElementById('cancelModal')).hide();
            location.reload();
        } else {
            alert(data.message || 'Error cancelling appointment');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error cancelling appointment');
    });
}

function checkInAppointment(appointmentId) {
    if (confirm('Mark this appointment as checked in?')) {
        fetch(`/appointments/${appointmentId}/checkin/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert(data.message || 'Error checking in appointment');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error checking in appointment');
        });
    }
}

function exportAppointments() {
    const form = document.getElementById('filterForm');
    const params = new URLSearchParams(new FormData(form));
    window.open(`/appointments/export/?${params.toString()}`, '_blank');
}
