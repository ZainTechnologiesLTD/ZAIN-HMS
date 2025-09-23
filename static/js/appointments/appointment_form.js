// Reset form function
function resetForm() {
    if (confirm('Are you sure you want to reset the form? All entered data will be lost.')) {
        document.getElementById('appointmentForm').reset();
        clearPatientSelection();
        clearDoctorSelection();
        document.getElementById('timeSlotsContainer').innerHTML = `
            <div class="text-muted text-center py-3">
                <i class="fas fa-info-circle me-2"></i>
                Select a doctor and date to view available time slots
            </div>
        `;
        updateAppointmentSummary();
    }
}
