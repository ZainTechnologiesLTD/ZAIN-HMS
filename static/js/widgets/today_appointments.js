document.addEventListener('DOMContentLoaded', function() {
    // Filter functionality
    document.querySelectorAll('.filter-chip').forEach(chip => {
        chip.addEventListener('click', function() {
            // Update active chip
            document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
            this.classList.add('active');

            // Filter appointments
            const filter = this.dataset.filter;
            filterAppointments(filter);
        });
    });

    // Auto-refresh every 5 minutes
    setInterval(refreshAppointments, 5 * 60 * 1000);
});

function filterAppointments(filter) {
    const appointments = document.querySelectorAll('.appointment-item');

    appointments.forEach(item => {
        if (filter === 'all' || item.dataset.status === filter) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
}

function refreshAppointments() {
    const refreshBtn = document.querySelector('.refresh-btn');
    const originalContent = refreshBtn.innerHTML;

    // Show loading state
    refreshBtn.innerHTML = '<i class="bi bi-arrow-clockwise" style="animation: spin 1s linear infinite;"></i>';

    fetch('{% url "appointments:today_appointments_widget" %}')
        .then(response => response.text())
        .then(html => {
            // Update the appointment list
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const newList = doc.querySelector('#appointmentList');
            const newStats = doc.querySelectorAll('.stat-number');

            if (newList) {
                document.getElementById('appointmentList').innerHTML = newList.innerHTML;
            }

            // Update stats
            if (newStats.length >= 4) {
                document.getElementById('totalToday').textContent = newStats[0].textContent;
                document.getElementById('pendingCount').textContent = newStats[1].textContent;
                document.getElementById('completedCount').textContent = newStats[2].textContent;
                document.getElementById('cancelledCount').textContent = newStats[3].textContent;
            }

            // Show success feedback
            showToast('Appointments refreshed', 'success');
        })
        .catch(error => {
            console.error('Error refreshing appointments:', error);
            showToast('Error refreshing appointments', 'error');
        })
        .finally(() => {
            // Restore original button
            refreshBtn.innerHTML = originalContent;
        });
}

function viewAppointment(appointmentId) {
    window.location.href = `{% url 'appointments:appointment_detail' '00000000-0000-0000-0000-000000000000' %}`.replace('00000000-0000-0000-0000-000000000000', appointmentId);
}

function editAppointment(appointmentId) {
    window.location.href = `{% url 'appointments:appointment_edit' '00000000-0000-0000-0000-000000000000' %}`.replace('00000000-0000-0000-0000-000000000000', appointmentId);
}

function exportTodayAppointments() {
    const today = new Date().toISOString().split('T')[0];
    window.open(`{% url 'appointments:export' %}?date_from=${today}&date_to=${today}`, '_blank');
}

function showToast(message, type = 'info') {
    // Create toast notification
    const toastContainer = document.getElementById('toastContainer') || createToastContainer();

    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-bg-${type === 'error' ? 'danger' : type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;

    toastContainer.appendChild(toast);

    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();

    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}
