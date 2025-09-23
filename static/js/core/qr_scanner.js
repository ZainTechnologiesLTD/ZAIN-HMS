let html5QrCode;
let isScanning = false;

document.addEventListener('DOMContentLoaded', function() {
    const startBtn = document.getElementById('start-camera');
    const stopBtn = document.getElementById('stop-camera');
    const statusDiv = document.getElementById('scanner-status');
    const searchInput = document.getElementById('manual-search');
    const searchBtn = document.getElementById('search-btn');
    const resultsDiv = document.getElementById('search-results');
    const resultsCount = document.getElementById('results-count');

    // Start camera scanning
    startBtn.addEventListener('click', function() {
        startScanning();
    });

    // Stop camera scanning
    stopBtn.addEventListener('click', function() {
        stopScanning();
    });

    // Manual search
    searchBtn.addEventListener('click', function() {
        const query = searchInput.value.trim();
        if (query) {
            performSearch('', query);
        }
    });

    // Search on Enter key
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchBtn.click();
        }
    });

    function startScanning() {
        if (isScanning) return;

        html5QrCode = new Html5Qrcode("camera-preview");

        updateStatus('info', "{% trans 'Starting camera...' %}");

        Html5Qrcode.getCameras().then(devices => {
            if (devices && devices.length) {
                const cameraId = devices[0].id;

                html5QrCode.start(
                    cameraId,
                    {
                        fps: 10,
                        qrbox: { width: 200, height: 200 }
                    },
                    (decodedText, decodedResult) => {
                        // QR code successfully scanned
                        updateStatus('success', "{% trans 'QR Code detected! Searching...' %}");
                        performSearch(decodedText);
                        stopScanning(); // Stop after successful scan
                    },
                    (errorMessage) => {
                        // Handle scan errors (mostly ignore)
                    }
                ).then(() => {
                    isScanning = true;
                    startBtn.style.display = 'none';
                    stopBtn.style.display = 'block';
                    updateStatus('info', "{% trans 'Scanning for QR codes...' %}");
                    document.getElementById('scanner-placeholder').style.display = 'none';
                }).catch(err => {
                    updateStatus('error', "{% trans 'Failed to start camera: ' %}" + err);
                });
            } else {
                updateStatus('error', "{% trans 'No cameras found on this device' %}");
            }
        }).catch(err => {
            updateStatus('error', "{% trans 'Error accessing cameras: ' %}" + err);
        });
    }

    function stopScanning() {
        if (html5QrCode && isScanning) {
            html5QrCode.stop().then(() => {
                isScanning = false;
                startBtn.style.display = 'block';
                stopBtn.style.display = 'none';
                updateStatus('info', "{% trans 'Camera stopped' %}");
                document.getElementById('scanner-placeholder').style.display = 'flex';
            }).catch(err => {
                updateStatus('error', "{% trans 'Error stopping camera: ' %}" + err);
            });
        }
    }

    function updateStatus(type, message) {
        statusDiv.className = `scanner-status ${type}`;
        statusDiv.textContent = message;
    }

    function performSearch(qrData = '', searchQuery = '') {
        const data = {
            qr_data: qrData,
            search_query: searchQuery
        };

        fetch('{% url "dashboard:qr_search" %}', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayResults(data.results);
                updateStatus('success', `{% trans 'Found' %} ${data.count} {% trans 'result(s)' %}`);
            } else {
                updateStatus('error', data.error);
                displayResults([]);
            }
        })
        .catch(error => {
            updateStatus('error', "{% trans 'Search failed: ' %}" + error);
            displayResults([]);
        });
    }

    function displayResults(results) {
        resultsCount.textContent = results.length;

        if (results.length === 0) {
            resultsDiv.innerHTML = `
                <div class="text-center text-muted py-3">
                    <i class="fas fa-search fa-2x mb-2"></i>
                    <p>{% trans "No results found" %}</p>
                </div>
            `;
            return;
        }

        const resultsHtml = results.map(result => {
            const typeColors = {
                'patient': 'primary',
                'doctor': 'success',
                'appointment': 'info',
                'lab_order': 'warning',
                'radiology_order': 'danger',
                'bill': 'secondary'
            };

            const typeLabels = {
                'patient': "{% trans 'Patient' %}",
                'doctor': "{% trans 'Doctor' %}",
                'appointment': "{% trans 'Appointment' %}",
                'lab_order': "{% trans 'Lab Order' %}",
                'radiology_order': "{% trans 'Radiology' %}",
                'bill': "{% trans 'Bill' %}"
            };

            const detailsHtml = Object.entries(result.details || {})
                .filter(([key, value]) => value)
                .map(([key, value]) => `<span class="me-3"><strong>${key}:</strong> ${value}</span>`)
                .join('');

            return `
                <div class="search-result">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <div class="d-flex align-items-center mb-2">
                                <span class="badge bg-${typeColors[result.type]} result-type-badge me-2">
                                    ${typeLabels[result.type]}
                                </span>
                                <h6 class="mb-0">${result.title}</h6>
                            </div>

                            ${result.subtitle ? `<p class="text-muted mb-2">${result.subtitle}</p>` : ''}

                            ${detailsHtml ? `<div class="result-details">${detailsHtml}</div>` : ''}
                        </div>

                        <a href="${result.url}" class="btn btn-sm btn-outline-primary">
                            <i class="fas fa-eye"></i>
                        </a>
                    </div>
                </div>
            `;
        }).join('');

        resultsDiv.innerHTML = resultsHtml;
    }

    // Add CSRF token to all requests
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (!csrfToken) {
        const meta = document.createElement('meta');
        meta.name = 'csrf-token';
        meta.content = '{{ csrf_token }}';
        document.getElementsByTagName('head')[0].appendChild(meta);
    }
});
