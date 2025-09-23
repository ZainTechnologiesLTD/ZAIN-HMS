// Global variables
let currentStep = 1;
let selectedPatient = null;
let selectedDepartment = null;
let selectedDate = null;
let selectedDoctor = null;
let selectedTimeSlot = null;
// Track the calendar context for month availability highlighting
let currentCalendarYear = null;   // e.g., 2025
let currentCalendarMonth = null;  // 1-12
let searchTimeout = null;

// Patient search pagination variables
let currentPage = 1;
let isLoadingMore = false;
let hasMorePatients = false;
let currentSearchQuery = '';

document.addEventListener('DOMContentLoaded', function() {
    initializeSearch();
    loadDepartments();
});

// Enhanced Patient Search Functionality
function initializeSearch() {
    const searchInput = document.getElementById('patientSearch');
    if (!searchInput) {
        console.error('Patient search input not found');
        return;
    }

    let searchTimeout = null;

    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();

        if (query.length >= 2) {
            searchTimeout = setTimeout(() => searchPatients(query), 300);
        } else if (query.length === 0) {
            // Load initial patients when search is cleared
            loadInitialPatients();
        } else {
            showSearchPrompt();
        }
    });

    // Load some initial patients on page load
    loadInitialPatients();
}

function loadInitialPatients() {
    console.log('Loading initial patients...');
    currentSearchQuery = '';
    currentPage = 1;

    fetch(`${window.APPOINTMENT_URLS.searchPatients}?q=&page=1&limit=10`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Initial patients loaded:', data);
            if (data.success && data.results) {
                displayPatients(data.results, data.pagination, true); // Replace existing
                showSearchHint(data.pagination.total_count);
            } else {
                showEmptyPatientState();
            }
        })
        .catch(error => {
            console.error('Error loading initial patients:', error);
            showEmptyPatientState();
        });
}

function searchPatients(query) {
    console.log('Searching for patients:', query);

    // Reset pagination for new search
    currentSearchQuery = query;
    currentPage = 1;
    isLoadingMore = false;

    const container = document.getElementById('patientResults');
    if (query.length >= 2) {
        container.innerHTML = '<div class="col-12 text-center text-white-50"><div class="spinner-border text-white" role="status"></div><p class="mt-2">Searching patients...</p></div>';
    }

    fetch(`${window.APPOINTMENT_URLS.searchPatients}?q=${encodeURIComponent(query)}&page=1&limit=20`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Search response:', data);
            if (data.success) {
                displayPatients(data.results || [], data.pagination, true); // Replace existing
            } else {
                console.error('Search failed:', data);
                showNoResultsFound(query);
            }
        })
        .catch(error => {
            console.error('Patient search error:', error);
            showErrorState();
        });
}

function loadMorePatients() {
    if (isLoadingMore || !hasMorePatients) return;

    isLoadingMore = true;
    currentPage++;

    console.log(`Loading more patients - page ${currentPage}`);

    // Show loading indicator
    const loadMoreBtn = document.getElementById('loadMorePatients');
    if (loadMoreBtn) {
        loadMoreBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
        loadMoreBtn.disabled = true;
    }

    fetch(`${window.APPOINTMENT_URLS.searchPatients}?q=${encodeURIComponent(currentSearchQuery)}&page=${currentPage}&limit=20`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                displayPatients(data.results || [], data.pagination, false); // Append to existing
            }
        })
        .catch(error => {
            console.error('Error loading more patients:', error);
            currentPage--; // Revert page increment
        })
        .finally(() => {
            isLoadingMore = false;
        });
}

function displayPatients(patients, pagination = null, replaceExisting = true) {
    const container = document.getElementById('patientResults');
    if (!container) {
        console.error('Patient results container not found');
        return;
    }

    if (replaceExisting && patients.length === 0) {
        showNoResultsFound();
        return;
    }

    console.log('Displaying patients:', patients, 'Pagination:', pagination);

    // Generate patient cards HTML (no inline onclick to avoid quoting issues)
    const patientsHTML = patients.map(patient => {
        // Safely escape patient data to prevent XSS
        const safeId = patient.id;
        const safeName = escapeHtml(patient.name || patient.text || 'Unknown');
        const safePhone = escapeHtml(patient.phone || '');
        const safeEmail = escapeHtml(patient.email || '');
        const safePatientId = escapeHtml(patient.patient_id || patient.id);
        const safeGender = escapeHtml(patient.gender || '');
        const safeAge = patient.age || '';

        // Generate initials for avatar
        const initials = safeName.split(' ').map(n => n.charAt(0)).join('').substring(0, 2).toUpperCase();

        return `
        <div class="col-md-6 col-lg-4 mb-3 patient-item" data-patient-id="${safeId}" data-patient-name="${safeName}" data-patient-phone="${safePhone}" data-patient-email="${safeEmail}">
            <div class="patient-card" role="button">
                <div class="d-flex align-items-center">
                    <div class="flex-shrink-0">
                        <div class="doctor-avatar" style="width: 50px; height: 50px; font-size: 1.1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                            ${initials}
                        </div>
                    </div>
                    <div class="flex-grow-1 ms-3">
                        <h6 class="mb-1">${safeName}</h6>
                        <p class="mb-1 text-muted small">
                            <i class="bi bi-person-badge me-1"></i>
                            ID: ${safePatientId}
                            ${safeAge ? ` • Age: ${safeAge}` : ''}
                            ${safeGender ? ` • ${safeGender}` : ''}
                        </p>
                        ${safePhone ? `<p class="mb-0 text-muted small"><i class="bi bi-phone me-1"></i>${safePhone}</p>` : ''}
                    </div>
                </div>
            </div>
        </div>
        `;
    }).join('');

    // Update pagination info
    if (pagination) {
        hasMorePatients = pagination.has_more;
    }

    if (replaceExisting) {
        // Replace all content
        let contentHTML = patientsHTML;

        // Add pagination controls if needed
        if (pagination && (pagination.has_more || pagination.current_page > 1)) {
            contentHTML += generatePaginationControls(pagination);
        }

        container.innerHTML = contentHTML;
        // Bind click handlers after inserting HTML
        bindPatientClickHandlers();
    } else {
        // Append to existing content (for "load more")
        const loadMoreBtn = document.getElementById('loadMorePatients');
        if (loadMoreBtn) {
            loadMoreBtn.remove(); // Remove old load more button
        }

        // Create temporary container and append patients
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = patientsHTML;

        while (tempDiv.firstChild) {
            container.appendChild(tempDiv.firstChild);
        }

        // Add pagination controls if still has more
        if (pagination && pagination.has_more) {
            container.innerHTML += generatePaginationControls(pagination);
        }
        // Bind click handlers for newly appended items
        bindPatientClickHandlers();
    }
}

// Bind click handlers to patient cards (avoids inline onclick quoting issues)
function bindPatientClickHandlers() {
    document.querySelectorAll('.patient-item .patient-card').forEach(card => {
        // Avoid attaching multiple listeners
        if (card._patientHandlerAttached) return;
        card._patientHandlerAttached = true;

        card.addEventListener('click', function() {
            const item = this.closest('.patient-item');
            if (!item) return;
            const id = item.dataset.patientId;
            const name = item.dataset.patientName || '';
            const phone = item.dataset.patientPhone || '';
            const email = item.dataset.patientEmail || '';
            selectPatient(id, name, phone, email);
        });
    });
}

function generatePaginationControls(pagination) {
    let controls = '';

    if (pagination.total_count > pagination.limit) {
        controls += `
        <div class="col-12 mt-3">
            <div class="text-center text-white-50">
                <small>Showing ${Math.min(pagination.current_page * pagination.limit, pagination.total_count)} of ${pagination.total_count} patients</small>
            </div>
        </div>
        `;
    }

    if (pagination.has_more) {
        controls += `
        <div class="col-12 mt-3 text-center">
            <button type="button" class="btn btn-outline-light btn-sm" id="loadMorePatients" onclick="loadMorePatients()">
                <i class="bi bi-plus-circle me-1"></i>
                Load More Patients
            </button>
        </div>
        `;
    }

    return controls;
}

function showSearchHint(totalCount) {
    if (totalCount > 10) {
        const container = document.getElementById('patientResults');
        const hintHTML = `
        <div class="col-12 mb-3">
            <div class="alert alert-info alert-sm" style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: white;">
                <i class="bi bi-info-circle me-2"></i>
                <strong>Tip:</strong> You have ${totalCount} patients. Use search to find specific patients quickly.
            </div>
        </div>
        `;
        container.insertAdjacentHTML('afterbegin', hintHTML);
    }
}

function showEmptyPatientState() {
    const container = document.getElementById('patientResults');
    if (!container) return;

    container.innerHTML = `
        <div class="col-12 text-center text-white-50">
            <i class="bi bi-person-search fs-1 mb-3"></i>
            <p>${window.APPOINTMENT_TRANSLATIONS.startTyping}</p>
            <small>Type at least 2 characters to search by name, phone, or patient ID</small>
        </div>
    `;
}

function showSearchPrompt() {
    const container = document.getElementById('patientResults');
    if (!container) return;

    container.innerHTML = `
        <div class="col-12 text-center text-white-50">
            <i class="bi bi-keyboard fs-1 mb-3"></i>
            <p>${window.APPOINTMENT_TRANSLATIONS.keepTyping}</p>
            <small>Type at least 2 characters to search patients</small>
        </div>
    `;
}

function showNoResultsFound(query = '') {
    const container = document.getElementById('patientResults');
    if (!container) return;

    container.innerHTML = `
        <div class="col-12 text-center text-white-50">
            <i class="bi bi-person-x fs-1 mb-3"></i>
            <p>${window.APPOINTMENT_TRANSLATIONS.noPatientsFound}${query ? ` for "${escapeHtml(query)}"` : ''}</p>
            <div class="mt-3">
                <small class="d-block mb-2">${window.APPOINTMENT_TRANSLATIONS.tryDifferentTerm}</small>
                <a href="/en/patients/create/" class="btn btn-outline-light btn-sm">
                    <i class="bi bi-person-plus me-1"></i>
                    Add New Patient
                </a>
            </div>
        </div>
    `;
}

function showErrorState() {
    const container = document.getElementById('patientResults');
    if (!container) return;

    container.innerHTML = `
        <div class="col-12 text-center text-white-50">
            <i class="bi bi-exclamation-triangle fs-1 mb-3"></i>
            <p>${window.APPOINTMENT_TRANSLATIONS.errorLoadingPatients}</p>
            <div class="mt-3">
                <button type="button" class="btn btn-outline-light btn-sm" onclick="loadInitialPatients()">
                    <i class="bi bi-arrow-clockwise me-1"></i>
                    Try Again
                </button>
            </div>
        </div>
    `;
}

// Utility function to escape HTML
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Patient Selection
function selectPatient(id, name, phone, email) {
    selectedPatient = { id, name, phone, email };

    // Update UI
    document.querySelectorAll('.patient-card').forEach(card => card.classList.remove('selected'));

    // Try to find the clicked patient card by data attribute and mark selected
    try {
        const cardEl = document.querySelector(`.patient-item[data-patient-id="${id}"] .patient-card`);
        if (cardEl) cardEl.classList.add('selected');
    } catch (e) {
        console.warn('Could not locate patient card element to mark selected', e);
    }

    // Fill hidden fields safely
    const selectedPatientInput = document.getElementById('selectedPatientId');
    if (selectedPatientInput) selectedPatientInput.value = id;

    const phoneField = document.querySelector('[name="patient_phone"]');
    if (phone && phoneField) phoneField.value = phone;

    const emailField = document.querySelector('[name="patient_email"]');
    if (email && emailField) emailField.value = email;

    // Enable next button if present
    const nextBtn = document.getElementById('nextBtn');
    if (nextBtn) nextBtn.disabled = false;

    console.log('Patient selected:', selectedPatient);
}

// Load Departments
function loadDepartments() {
    // Fetch departments from API
    fetch('/en/appointments/api/enhanced/departments/')
        .then(response => response.json())
        .then(data => {
            const departments = data.results || [];
            const container = document.getElementById('departmentList');

            console.log(`Loaded ${departments.length} departments:`, departments);

            if (departments.length === 0) {
                container.innerHTML = `
                    <div class="col-12 text-center">
                        <div class="alert alert-info">
                            <i class="bi bi-info-circle me-2"></i>
                            No departments available. Please ensure doctors are registered with specializations.
                        </div>
                    </div>
                `;
                return;
            }

            container.innerHTML = departments.map(dept => `
                <div class="col-md-6 col-lg-4 mb-3">
                    <div class="department-card" data-department="${dept.value || dept.name}" onclick="selectDepartment('${dept.name}', '${dept.value || dept.name}')">
                        <div class="text-center">
                            <i class="bi bi-${dept.icon} fs-1 mb-3"></i>
                            <h6>${dept.name}</h6>
                            <p class="small text-muted mb-0">${dept.description}</p>
                        </div>
                    </div>
                </div>
            `).join('');
        })
        .catch(error => {
            console.error('Error loading departments:', error);
            const container = document.getElementById('departmentList');
            container.innerHTML = `
                <div class="col-12 text-center">
                    <div class="alert alert-danger">
                        <i class="bi bi-exclamation-triangle me-2"></i>
                        Error loading departments. Please refresh the page.
                    </div>
                </div>
            `;
        });
}

// Department Selection
function selectDepartment(name, value) {
    selectedDepartment = value || name;  // Use database value (specialization code) for API calls

    // Update UI
    document.querySelectorAll('.department-card').forEach(card => card.classList.remove('selected'));
    try {
        const el = document.querySelector(`.department-card[data-department="${selectedDepartment}"]`);
        if (el) el.classList.add('selected');
    } catch (e) {
        console.warn('Could not locate department card to mark selected', e);
    }

    // Fill hidden field with human readable name for form
    document.getElementById('selectedDepartment').value = name;

    // Enable next button
    document.getElementById('nextBtn').disabled = false;

    console.log('Department selected:', name, 'Code:', selectedDepartment);

    // Refresh availability highlighting for current calendar month
    updateCalendarAvailability();
}

// Calendar Initialization
function initializeCalendar() {
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth() + 1; // 1-12
    renderCalendar(year, month);
}

function changeCalendarMonth(offset) {
    if (!currentCalendarYear || !currentCalendarMonth) return;
    let y = currentCalendarYear;
    let m = currentCalendarMonth + offset; // 1-12 space
    if (m < 1) {
        m = 12;
        y -= 1;
    } else if (m > 12) {
        m = 1;
        y += 1;
    }
    renderCalendar(y, m);
}

function renderCalendar(year, month1) {
    // Set globals for availability fetch
    currentCalendarYear = year;
    currentCalendarMonth = month1; // 1-12

    const calendarEl = document.getElementById('appointmentCalendar');
    const now = new Date();
    const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const month0 = month1 - 1; // JS Date expects 0-11

    const firstDay = new Date(year, month0, 1).getDay();
    const daysInMonth = new Date(year, month0 + 1, 0).getDate();

    const monthName = new Date(year, month0, 1).toLocaleString(undefined, { month: 'long' });

    let calendarHtml = `
        <div class="d-flex justify-content-between align-items-center mb-2">
            <button type="button" class="btn btn-sm btn-outline-secondary" onclick="changeCalendarMonth(-1)" aria-label="Previous Month">&laquo;</button>
            <div class="fw-bold">${monthName} ${year}</div>
            <button type="button" class="btn btn-sm btn-outline-secondary" onclick="changeCalendarMonth(1)" aria-label="Next Month">&raquo;</button>
        </div>
        <div class="calendar-grid">
    `;

    // Days of week header
    const daysOfWeek = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    calendarHtml += '<div class="row mb-2">';
    daysOfWeek.forEach(day => {
        calendarHtml += `<div class="col text-center small fw-bold">${day}</div>`;
    });
    calendarHtml += '</div>';

    let dayCount = 1;
    for (let week = 0; week < 6; week++) {
        calendarHtml += '<div class="row mb-1">';
        for (let day = 0; day < 7; day++) {
            if ((week === 0 && day < firstDay) || dayCount > daysInMonth) {
                calendarHtml += '<div class="col p-1"></div>';
            } else {
                const date = new Date(year, month0, dayCount);
                const y = date.getFullYear();
                const m = String(date.getMonth() + 1).padStart(2, '0');
                const d = String(date.getDate()).padStart(2, '0');
                const dateStr = `${y}-${m}-${d}`;
                const isToday = (date.getTime() === todayStart.getTime());
                const isPast = (date < todayStart);
                calendarHtml += `
                    <div class="col p-1">
                        <div class="calendar-day ${isToday ? 'selected' : ''}"
                             data-day="${dayCount}" data-date="${dateStr}"
                             ${!isPast ? `onclick="selectDate('${dateStr}')"` : 'style="opacity: 0.3; cursor: not-allowed;"'}>
                            ${dayCount}
                        </div>
                    </div>
                `;
                dayCount++;
            }
        }
        calendarHtml += '</div>';
        if (dayCount > daysInMonth) break;
    }
    calendarHtml += '</div>';
    calendarEl.innerHTML = calendarHtml;

    // Fetch and apply availability for the newly rendered month
    updateCalendarAvailability();
}

// Date Selection
function selectDate(dateStr) {
    selectedDate = dateStr;

    // Update UI
    document.querySelectorAll('.calendar-day').forEach(day => day.classList.remove('selected'));
    try {
        const el = document.querySelector(`.calendar-day[data-date="${dateStr}"]`);
        if (el) el.classList.add('selected');
    } catch (e) {
        console.warn('Could not locate calendar-day element to mark selected', e);
    }

    // Fill hidden field
    document.getElementById('selectedDate').value = dateStr;

    // Load doctors for this date and department
    loadDoctors(dateStr, selectedDepartment);

    console.log('Date selected:', selectedDate);
}

// Load Doctors
function loadDoctors(date, department) {
    const url = `${window.APPOINTMENT_URLS.getDoctorsByDepartment.replace('0/', `${department}/`)}?date=${date}`;

    fetch(url)
        .then(response => response.json())
        .then(data => {
            displayDoctors(data.results || []);
        })
        .catch(error => {
            console.error('Error loading doctors:', error);
            document.getElementById('doctorList').innerHTML = `
                <div class="text-center text-muted">
                    <i class="bi bi-exclamation-triangle fs-1 mb-3"></i>
                    <p>${window.APPOINTMENT_TRANSLATIONS.errorLoadingDoctors}</p>
                </div>
            `;
        });
}

function displayDoctors(doctors) {
    const container = document.getElementById('doctorList');

    if (doctors.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted">
                <i class="bi bi-person-x fs-1 mb-3"></i>
                <p>${window.APPOINTMENT_TRANSLATIONS.noDoctorsAvailable}</p>
            </div>
        `;
        return;
    }

    container.innerHTML = doctors.map(doctor => `
        <div class="doctor-card mb-3" data-doctor-id="${doctor.id}" onclick="selectDoctor(${doctor.id}, '${doctor.name}', '${doctor.specialization}')">
            <div class="text-center">
                <div class="doctor-avatar">
                    ${doctor.name.split(' ').map(n => n[0]).join('').substring(0, 2)}
                </div>
                <h6 class="mb-1">${doctor.name}</h6>
                <p class="small text-muted mb-2">${doctor.specialization}</p>
                <div class="small">
                    <i class="bi bi-clock me-1"></i>
                    Available slots: ${doctor.available_slots || 0}
                </div>
            </div>
        </div>
    `).join('');
}

// Doctor Selection
function selectDoctor(id, name, specialization) {
    selectedDoctor = { id, name, specialization };

    // Update UI
    document.querySelectorAll('.doctor-card').forEach(card => card.classList.remove('selected'));
    try {
        const el = document.querySelector(`.doctor-card[data-doctor-id="${id}"]`);
        if (el) el.classList.add('selected');
    } catch (e) {
        console.warn('Could not locate doctor card element to mark selected', e);
    }

    // Fill hidden field
    document.getElementById('selectedDoctorId').value = id;

    // Enable next button
    document.getElementById('nextBtn').disabled = false;

    console.log('Doctor selected:', selectedDoctor);

    // Refresh availability highlighting when doctor changes
    updateCalendarAvailability();
}

// Load Time Slots
function loadTimeSlots() {
    if (!selectedDoctor || !selectedDate) return;
    // Use enhanced endpoint which returns start/end and booking flag
    const url = `${window.APPOINTMENT_URLS.getTimeSlots}?doctor_id=${selectedDoctor.id}&date=${selectedDate}`;

    fetch(url)
        .then(response => response.json())
        .then(data => {
            // enhanced endpoint returns { time_slots: [...] }
            displayTimeSlots(data.time_slots || []);
            updateDoctorScheduleInfo();
        })
        .catch(error => {
            console.error('Error loading time slots:', error);
        });
}

function displayTimeSlots(slots) {
    const container = document.getElementById('timeSlots');

    if (slots.length === 0) {
        container.innerHTML = `
            <div class="col-12 text-center text-muted">
                <i class="bi bi-calendar-x fs-1 mb-3"></i>
                <p>${window.APPOINTMENT_TRANSLATIONS.noTimeSlots}</p>
            </div>
        `;
        return;
    }

    container.innerHTML = slots.map(slot => `
        <div class="col-md-4 col-lg-3 mb-3">
            <div class="time-slot ${slot.is_booked ? 'booked' : ''}"
                 data-start="${slot.start_time}"
                 data-end="${slot.end_time}"
                 data-capacity="${typeof slot.capacity !== 'undefined' ? slot.capacity : ''}"
                 data-booked="${typeof slot.booked !== 'undefined' ? slot.booked : ''}"
                 data-available="${typeof slot.available !== 'undefined' ? slot.available : ''}"
                 data-serial="${slot.serial_number ? slot.serial_number : ''}"
                 ${!slot.is_booked ? `onclick="selectTimeSlot('${slot.start_time}', '${slot.end_time}', ${slot.capacity ?? 0}, ${slot.booked ?? 0}, ${slot.available ?? 0}, '${slot.serial_number ?? ''}')"` : ''}>
                <div class="fw-bold">${slot.start_time} - ${slot.end_time}</div>
                <div class="small">
                    ${slot.is_booked ? window.APPOINTMENT_TRANSLATIONS.full : window.APPOINTMENT_TRANSLATIONS.available}
                </div>
                ${slot.serial_number ? `<div class="small text-success">Next Serial: ${slot.serial_number}</div>` : ''}
                ${typeof slot.capacity !== 'undefined' ? `<div class="small text-muted">${slot.booked}/${slot.capacity} booked</div>` : ''}
            </div>
        </div>
    `).join('');
}

// Time Slot Selection
function selectTimeSlot(startTime, endTime, capacity = 0, booked = 0, available = 0, serial = '') {
    selectedTimeSlot = { startTime, endTime, capacity, booked, available, serial };

    // Update UI
    document.querySelectorAll('.time-slot').forEach(slot => slot.classList.remove('selected'));
    try {
        const el = document.querySelector(`.time-slot[data-start="${startTime}"][data-end="${endTime}"]`);
        if (el) el.classList.add('selected');
    } catch (e) {
        console.warn('Could not locate time-slot element to mark selected', e);
    }

    // Fill hidden fields
    document.getElementById('selectedTime').value = startTime;
    document.getElementById('selectedSlotStart').value = startTime;
    document.getElementById('selectedSlotEnd').value = endTime;

    // Enable next button
    document.getElementById('nextBtn').disabled = false;

    updateSelectedSummary();
    console.log('Time slot selected:', selectedTimeSlot);
}

// Update Doctor Schedule Info
function updateDoctorScheduleInfo() {
    const container = document.getElementById('doctorScheduleInfo');
    if (!selectedDoctor) return;

    container.innerHTML = `
        <div class="d-flex align-items-center">
            <div class="doctor-avatar me-3" style="width: 50px; height: 50px; font-size: 1.2rem;">
                ${selectedDoctor.name.split(' ').map(n => n[0]).join('').substring(0, 2)}
            </div>
            <div>
                <h6 class="mb-1">Dr. ${selectedDoctor.name}</h6>
                <p class="mb-1 small">${selectedDoctor.specialization}</p>
                <p class="mb-0 small">
                    <i class="bi bi-calendar-date me-1"></i>
                    ${new Date(selectedDate).toLocaleDateString()}
                </p>
            </div>
        </div>
    `;
}

// Update Selected Summary
function updateSelectedSummary() {
    const container = document.getElementById('selectedSummary');

    let summary = '<div class="small">';
    if (selectedPatient) summary += `<p><strong>Patient:</strong> ${selectedPatient.name}</p>`;
    if (selectedDepartment) summary += `<p><strong>Department:</strong> ${selectedDepartment}</p>`;
    if (selectedDoctor) summary += `<p><strong>Doctor:</strong> Dr. ${selectedDoctor.name}</p>`;
    if (selectedDate) summary += `<p><strong>Date:</strong> ${new Date(selectedDate).toLocaleDateString()}</p>`;
    if (selectedTimeSlot) {
        summary += `<p><strong>Time:</strong> ${selectedTimeSlot.startTime} - ${selectedTimeSlot.endTime}</p>`;
        if (typeof selectedTimeSlot.capacity !== 'undefined' && selectedTimeSlot.capacity) {
            summary += `<p class="mb-1"><strong>Capacity:</strong> ${selectedTimeSlot.capacity}</p>`;
            summary += `<p class="mb-1"><strong>Booked:</strong> ${selectedTimeSlot.booked}</p>`;
            summary += `<p class="mb-1"><strong>Available:</strong> ${selectedTimeSlot.available}</p>`;
        }
        if (selectedTimeSlot.serial) {
            summary += `<p class="text-success"><strong>Next Serial:</strong> ${selectedTimeSlot.serial}</p>`;
        }
    }
    summary += '</div>';

    container.innerHTML = summary;
}

// Step Management
function changeStep(direction) {
    const newStep = currentStep + direction;

    if (newStep < 1 || newStep > 5) return;

    // Validate current step
    if (direction === 1 && !validateCurrentStep()) {
        return;
    }

    // Hide current step
    document.getElementById(`step${currentStep}`).classList.remove('active');
    document.querySelector(`[data-step="${currentStep}"]`).classList.remove('active');

    // Show new step
    currentStep = newStep;
    document.getElementById(`step${currentStep}`).classList.add('active');
    document.querySelector(`[data-step="${currentStep}"]`).classList.add('active');

    // Update completed steps
    for (let i = 1; i < currentStep; i++) {
        document.querySelector(`[data-step="${i}"]`).classList.add('completed');
    }

    // Update navigation buttons
    updateNavigationButtons();

    // Initialize step-specific functionality
    initializeStep(currentStep);
}

function validateCurrentStep() {
    switch (currentStep) {
        case 1:
            if (!selectedPatient) {
                alert(window.APPOINTMENT_TRANSLATIONS.selectPatient);
                return false;
            }
            break;
        case 2:
            if (!selectedDepartment) {
                alert(window.APPOINTMENT_TRANSLATIONS.selectDepartment);
                return false;
            }
            break;
        case 3:
            if (!selectedDate || !selectedDoctor) {
                alert(window.APPOINTMENT_TRANSLATIONS.selectDateDoctor);
                return false;
            }
            break;
        case 4:
            if (!selectedTimeSlot) {
                alert(window.APPOINTMENT_TRANSLATIONS.selectTimeSlot);
                return false;
            }
            break;
    }
    return true;
}

function initializeStep(step) {
    switch (step) {
        case 3:
            initializeCalendar();
            break;
        case 4:
            loadTimeSlots();
            break;
        case 5:
            updateSelectedSummary();
            break;
    }

    // Reset next button state
    document.getElementById('nextBtn').disabled = (step === 3 && (!selectedDate || !selectedDoctor)) ||
                                                 (step === 4 && !selectedTimeSlot);
}

function updateNavigationButtons() {
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const submitBtn = document.getElementById('submitBtn');

    prevBtn.style.display = currentStep > 1 ? 'inline-block' : 'none';

    if (currentStep === 5) {
        nextBtn.style.display = 'none';
        submitBtn.style.display = 'inline-block';
    } else {
        nextBtn.style.display = 'inline-block';
        submitBtn.style.display = 'none';
    }
}

// Month availability: fetch and apply highlighting to the calendar
function updateCalendarAvailability() {
    if (!currentCalendarYear || !currentCalendarMonth) return;
    // Require at least department or doctor to be selected
    if (!(selectedDoctor && selectedDoctor.id) && !selectedDepartment) return;
    fetchMonthAvailability(currentCalendarYear, currentCalendarMonth);
}

function fetchMonthAvailability(year, month) {
    const params = new URLSearchParams({ year: String(year), month: String(month) });
    if (selectedDoctor && selectedDoctor.id) {
        params.set('doctor_id', String(selectedDoctor.id));
    } else if (selectedDepartment) {
        params.set('department', selectedDepartment);
    }
    const url = `${window.APPOINTMENT_URLS.getMonthAvailability}?${params.toString()}`;
    fetch(url)
        .then(resp => resp.json())
        .then(data => {
            const days = Array.isArray(data.available_days) ? data.available_days : [];
            applyAvailabilityToCalendar(days);
        })
        .catch(err => {
            console.error('Error fetching month availability:', err);
            applyAvailabilityToCalendar([]);
        });
}

function applyAvailabilityToCalendar(availableDays) {
    // Clear previous marks
    document.querySelectorAll('.calendar-day.has-slots').forEach(el => el.classList.remove('has-slots'));

    if (!Array.isArray(availableDays) || availableDays.length === 0) return;

    // Determine today's start to avoid marking past days
    const now = new Date();
    const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());

    availableDays.forEach(day => {
        const el = document.querySelector(`.calendar-day[data-day="${day}"]`);
        if (!el) return;
        const dateStr = el.getAttribute('data-date');
        if (!dateStr) return;
        const [y, m, d] = dateStr.split('-').map(Number);
        const cellDate = new Date(y, m - 1, d);
        if (cellDate < todayStart) return; // don't mark past days
        el.classList.add('has-slots');
    });
}

// Submit Appointment
function submitAppointment() {
    const form = document.getElementById('appointmentForm');
    const formData = new FormData(form);

    // Show loading
    document.getElementById('navigationButtons').style.display = 'none';
    document.getElementById('loadingSpinner').style.display = 'block';

    fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('loadingSpinner').style.display = 'none';

        if (data.success) {
            showSuccessAnimation(data.appointment);
        } else {
            alert('Error: ' + (data.message || 'Failed to create appointment'));
            document.getElementById('navigationButtons').style.display = 'block';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('loadingSpinner').style.display = 'none';
        alert(window.APPOINTMENT_TRANSLATIONS.errorOccurred);
        document.getElementById('navigationButtons').style.display = 'block';
    });
}

function showSuccessAnimation(appointment) {
    // Hide all steps
    document.querySelectorAll('.wizard-step').forEach(step => step.classList.remove('active'));

    // Update appointment details
    const detailsHtml = `
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="bg-white text-dark p-4 rounded">
                    <h6 class="mb-3">${window.APPOINTMENT_TRANSLATIONS.appointmentDetails}</h6>
                    <p><strong>${window.APPOINTMENT_TRANSLATIONS.appointmentNumber}</strong> ${appointment.appointment_number}</p>
                    <p><strong>${window.APPOINTMENT_TRANSLATIONS.serialNumber}</strong> ${appointment.serial_number}</p>
                    <p><strong>${window.APPOINTMENT_TRANSLATIONS.patient}</strong> ${appointment.patient_name}</p>
                    <p><strong>${window.APPOINTMENT_TRANSLATIONS.doctor}</strong> Dr. ${appointment.doctor_name}</p>
                    <p><strong>${window.APPOINTMENT_TRANSLATIONS.dateTime}</strong> ${appointment.date} at ${appointment.time}</p>
                    <div class="text-center mt-3">
                        <div class="bg-light p-2 rounded">
                            <small class="text-muted">${window.APPOINTMENT_TRANSLATIONS.barcode}</small><br>
                            <code>${appointment.barcode}</code>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    document.getElementById('appointmentDetails').innerHTML = detailsHtml;

    // Update print link
    document.getElementById('printAppointment').href = `/appointments/${appointment.id}/print/`;

    // Show success animation
    document.getElementById('successAnimation').classList.add('show');
}

// Follow-up functionality
document.addEventListener('DOMContentLoaded', function() {
    updateNavigationButtons();

    // Handle follow-up checkbox
    const followUpCheckbox = document.getElementById('is_follow_up');
    const previousAppointmentField = document.getElementById('previousAppointmentField');
    const previousAppointmentSelect = document.getElementById('previous_appointment');

    followUpCheckbox.addEventListener('change', function() {
        if (this.checked) {
            previousAppointmentField.style.display = 'block';
            loadPreviousAppointments();
        } else {
            previousAppointmentField.style.display = 'none';
            previousAppointmentSelect.innerHTML = '<option value="">Select previous appointment</option>';
        }
    });
});

// Load previous appointments for follow-up
function loadPreviousAppointments() {
    const patientId = document.getElementById('selectedPatientId').value;
    if (!patientId) {
        alert('Please select a patient first');
        document.getElementById('is_follow_up').checked = false;
        document.getElementById('previousAppointmentField').style.display = 'none';
        return;
    }

    fetch(`/appointments/api/patient/${patientId}/previous-appointments/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const select = document.getElementById('previous_appointment');
                select.innerHTML = '<option value="">Select previous appointment</option>';

                data.appointments.forEach(appointment => {
                    const option = document.createElement('option');
                    option.value = appointment.id;
                    option.textContent = appointment.display_text;
                    option.title = `${appointment.chief_complaint}`;
                    select.appendChild(option);
                });
            } else {
                alert('Error loading previous appointments: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error loading previous appointments');
        });
}
