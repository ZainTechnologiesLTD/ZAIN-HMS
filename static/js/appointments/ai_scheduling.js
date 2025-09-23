let selectedDoctor = null;
let selectedTimeSlot = null;

function selectDoctor(doctorId) {
    // Remove previous selection
    document.querySelectorAll('.doctor-selection-card').forEach(card => {
        card.classList.remove('selected');
    });

    // Select new doctor
    const selectedCard = document.querySelector(`[data-doctor-id="${doctorId}"]`);
    selectedCard.classList.add('selected');

    // Update form
    document.querySelector(`input[name="doctor"][value="${doctorId}"]`).checked = true;
    selectedDoctor = doctorId;

    // Load optimized slots if date is selected
    const appointmentDate = document.getElementById('appointmentDate').value;
    if (appointmentDate) {
        loadOptimizedSlots();
    }
}

function selectTimeSlot(element) {
    // Remove previous selection
    document.querySelectorAll('.time-slot').forEach(slot => {
        slot.classList.remove('selected');
    });

    // Select new time slot
    element.classList.add('selected');

    // Update form
    const time = element.dataset.time;
    const date = element.dataset.date;

    document.querySelector(`input[name="appointment_time"][value="${time}"]`).checked = true;

    // Update appointment date if different
    document.getElementById('appointmentDate').value = date;

    selectedTimeSlot = {time: time, date: date};

    // Load AI insights for this selection
    loadAIInsights();
}

function loadOptimizedSlots() {
    if (!selectedDoctor) {
        alert('Please select a doctor first');
        return;
    }

    const appointmentDate = document.getElementById('appointmentDate').value;
    const duration = document.getElementById('duration').value;

    if (!appointmentDate) return;

    // Show loading state
    document.getElementById('optimizedSchedule').innerHTML = `
        <div class="text-center py-4">
            <i class="fas fa-spinner fa-spin fa-2x"></i>
            <p class="mt-2">Loading AI-optimized slots...</p>
        </div>
    `;

    // Make API call to get optimized slots
    fetch(`/appointments/api/ai-scheduling/?action=optimize_slots&doctor_id=${selectedDoctor}&date=${appointmentDate}&duration=${duration}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderOptimizedSlots(data.slots, appointmentDate);
            } else {
                document.getElementById('optimizedSchedule').innerHTML = `
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle"></i>
                        No available slots found for this date.
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error loading slots:', error);
            document.getElementById('optimizedSchedule').innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle"></i>
                    Error loading time slots. Please try again.
                </div>
            `;
        });
}

function renderOptimizedSlots(slots, date) {
    const dayName = new Date(date).toLocaleDateString('en-US', { weekday: 'long' });
    const dateFormatted = new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

    let html = `
        <div class="mb-4">
            <h6 class="border-bottom pb-2">
                ${dayName}, ${dateFormatted}
                <small class="text-muted">(${slots.length} slots available)</small>
            </h6>
    `;

    slots.forEach(slot => {
        const recommendationClass = slot.recommendation.toLowerCase().replace('_', '-');
        const recommendationText = slot.recommendation.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());

        let icon = 'fas fa-clock';
        if (slot.recommendation === 'HIGHLY_RECOMMENDED') icon = 'fas fa-star';
        else if (slot.recommendation === 'RECOMMENDED') icon = 'fas fa-thumbs-up';
        else if (slot.recommendation === 'NOT_RECOMMENDED') icon = 'fas fa-exclamation-triangle';

        html += `
            <div class="time-slot ${recommendationClass}"
                 data-time="${slot.time}"
                 data-date="${date}"
                 onclick="selectTimeSlot(this)">
                <div class="ai-score-badge">
                    ${slot.ai_score.toFixed(1)}
                </div>

                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${slot.time}</strong>
                        <div class="mt-1">
                            <span class="recommendation-indicator ${recommendationClass}">
                                <i class="${icon}"></i> ${recommendationText}
                            </span>
                        </div>
                    </div>
                </div>

                <input type="radio" name="appointment_time" value="${slot.time}"
                       class="d-none time-radio">
            </div>
        `;
    });

    html += '</div>';
    document.getElementById('optimizedSchedule').innerHTML = html;
}

function loadAIInsights() {
    if (!selectedDoctor || !selectedTimeSlot) return;

    const patientId = document.getElementById('patientSelect').value;
    if (!patientId) return;

    const datetime = `${selectedTimeSlot.date} ${selectedTimeSlot.time}`;

    fetch(`/appointments/api/ai-scheduling/?action=predict_no_show&doctor_id=${selectedDoctor}&patient_id=${patientId}&datetime=${encodeURIComponent(datetime)}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAIInsights(data);
            }
        })
        .catch(error => {
            console.error('Error loading AI insights:', error);
        });
}

function showAIInsights(data) {
    const panel = document.getElementById('aiInsightsPanel');
    const content = document.getElementById('aiInsightsContent');

    let riskClass = 'success';
    let riskIcon = 'fas fa-check-circle';

    if (data.risk_level === 'HIGH') {
        riskClass = 'danger';
        riskIcon = 'fas fa-exclamation-triangle';
    } else if (data.risk_level === 'MEDIUM') {
        riskClass = 'warning';
        riskIcon = 'fas fa-exclamation-circle';
    }

    let html = `
        <div class="alert alert-${riskClass} alert-sm">
            <i class="${riskIcon}"></i>
            <strong>No-show Risk: ${data.risk_level}</strong>
            <br>
            <small>Probability: ${(data.no_show_probability * 100).toFixed(1)}%</small>
        </div>
    `;

    if (data.recommendations && data.recommendations.length > 0) {
        html += '<div class="mt-2"><strong>Recommendations:</strong><ul class="mt-1 mb-0">';
        data.recommendations.forEach(rec => {
            html += `<li><small>${rec}</small></li>`;
        });
        html += '</ul></div>';
    }

    content.innerHTML = html;
    panel.style.display = 'block';
}

// Initialize patient search
document.getElementById('patientSearch').addEventListener('input', function(e) {
    const searchTerm = e.target.value.toLowerCase();
    const options = document.querySelectorAll('#patientSelect option');

    options.forEach(option => {
        if (option.value === '') return; // Skip placeholder

        const text = option.textContent.toLowerCase();
        option.style.display = text.includes(searchTerm) ? 'block' : 'none';
    });
});

// Load AI insights when patient changes
document.getElementById('patientSelect').addEventListener('change', function() {
    if (selectedTimeSlot) {
        loadAIInsights();
    }
});

// Initialize form validation
document.getElementById('aiSchedulingForm').addEventListener('submit', function(e) {
    if (!selectedDoctor) {
        e.preventDefault();
        alert('Please select a doctor');
        return;
    }

    if (!document.getElementById('appointmentDate').value) {
        e.preventDefault();
        alert('Please select an appointment date');
        return;
    }

    if (!selectedTimeSlot) {
        e.preventDefault();
        alert('Please select a time slot');
        return;
    }

    if (!document.getElementById('patientSelect').value) {
        e.preventDefault();
        alert('Please select a patient');
        return;
    }
});

// Set minimum date to today
document.getElementById('appointmentDate').min = new Date().toISOString().split('T')[0];
