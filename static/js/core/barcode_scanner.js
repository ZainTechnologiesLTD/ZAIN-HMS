let currentStream = null;
let flashSupported = false;

// Initialize barcode input as default
document.addEventListener('DOMContentLoaded', function() {
    console.log('Barcode scanner page loaded');
    console.log('ZXing available:', typeof ZXing !== 'undefined');
    console.log('Camera API available:', navigator.mediaDevices ? 'Yes' : 'No');

    selectScannerMethod('barcode');

    // Auto-search when barcode is entered
    document.getElementById('barcode-input').addEventListener('input', function(e) {
        const value = e.target.value.trim();
        if (value.length >= 8) {  // Minimum barcode length
            searchBarcode();
        }
    });

    // Manual search on Enter
    document.getElementById('manual-search').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            manualSearch();
        }
    });
});

function selectScannerMethod(method) {
    // Reset active states
    document.querySelectorAll('.scanner-method').forEach(m => m.classList.remove('active'));
    document.querySelectorAll('.barcode-input-section, .camera-section').forEach(s => s.classList.remove('active'));

    // Set active method
    document.getElementById(method + '-method').classList.add('active');

    if (method === 'barcode') {
        document.getElementById('barcode-input-section').classList.add('active');
        document.getElementById('barcode-input').focus();
        stopCamera();
    } else if (method === 'camera') {
        document.getElementById('camera-section').classList.add('active');
        // Auto-start camera when camera method is selected
        setTimeout(() => {
            startCamera();
        }, 100);
    }
}

function searchBarcode() {
    const barcodeValue = document.getElementById('barcode-input').value.trim();

    if (!barcodeValue) {
        showError('{% trans "Please enter a barcode" %}');
        return;
    }

    showLoading(true);
    hideMessages();

    fetch('{% url "core:barcode_search" %}', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({
            'barcode_data': barcodeValue
        })
    })
    .then(response => response.json())
    .then(data => {
        showLoading(false);

        if (data.success && data.results.length > 0) {
            displayResults(data.results);
            showSuccess(`{% trans "Found" %} ${data.results.length} {% trans "record(s)" %}`);
        } else {
            showError('{% trans "No records found for this barcode" %}');
            hideResults();
        }
    })
    .catch(error => {
        showLoading(false);
        showError('{% trans "Search failed. Please try again." %}');
        console.error('Search error:', error);
    });
}

function manualSearch() {
    const searchQuery = document.getElementById('manual-search').value.trim();

    if (!searchQuery) {
        showError('{% trans "Please enter search terms" %}');
        return;
    }

    showLoading(true);
    hideMessages();

    fetch('{% url "core:manual_search" %}', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({
            'query': searchQuery
        })
    })
    .then(response => response.json())
    .then(data => {
        showLoading(false);

        if (data.success && data.results.length > 0) {
            displayResults(data.results);
            showSuccess(`{% trans "Found" %} ${data.results.length} {% trans "record(s)" %}`);
        } else {
            showError('{% trans "No records found" %}');
            hideResults();
        }
    })
    .catch(error => {
        showLoading(false);
        showError('{% trans "Search failed. Please try again." %}');
        console.error('Search error:', error);
    });
}

function displayResults(results) {
    const resultsList = document.getElementById('results-list');
    resultsList.innerHTML = '';

    results.forEach(result => {
        const resultItem = document.createElement('div');
        resultItem.className = 'result-item';
        resultItem.onclick = () => window.open(result.url, '_blank');

        resultItem.innerHTML = `
            <div class="result-type">${result.type.replace('_', ' ')}</div>
            <div class="result-title">${result.title}</div>
            <div class="result-subtitle">${result.subtitle}</div>
        `;

        resultsList.appendChild(resultItem);
    });

    document.getElementById('search-results').classList.add('active');
}

function clearInput() {
    document.getElementById('barcode-input').value = '';
    document.getElementById('manual-search').value = '';
    hideResults();
    hideMessages();
    document.getElementById('barcode-input').focus();
}

function hideResults() {
    document.getElementById('search-results').classList.remove('active');
}

function showLoading(show) {
    const spinner = document.getElementById('loading-spinner');
    if (show) {
        spinner.classList.add('active');
    } else {
        spinner.classList.remove('active');
    }
}

function showError(message) {
    const errorDiv = document.getElementById('error-message');
    errorDiv.textContent = message;
    errorDiv.classList.add('active');
}

function showSuccess(message) {
    const successDiv = document.getElementById('success-message');
    successDiv.textContent = message;
    successDiv.classList.add('active');
}

function hideMessages() {
    document.getElementById('error-message').classList.remove('active');
    document.getElementById('success-message').classList.remove('active');
}

// Camera and Barcode Detection functions
let codeReader = null;

async function startCamera() {
    try {
        // Check if navigator.mediaDevices is available
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            throw new Error('Camera API not supported in this browser');
        }

        console.log('Requesting camera access...');

        const constraints = {
            video: {
                facingMode: 'environment', // Use back camera
                width: { ideal: 1280 },
                height: { ideal: 720 }
            }
        };

        currentStream = await navigator.mediaDevices.getUserMedia(constraints);
        const video = document.getElementById('camera-feed');
        video.srcObject = currentStream;

        // Wait for video to be ready
        video.onloadedmetadata = function() {
            video.play();
            console.log('Camera stream ready');

            // Start barcode detection after video is ready
            setTimeout(() => {
                startBarcodeDetection();
            }, 1000);
        };

        // Check for flash support
        const track = currentStream.getVideoTracks()[0];
        const capabilities = track.getCapabilities();
        flashSupported = 'torch' in capabilities;

        document.getElementById('start-camera').style.display = 'none';
        document.getElementById('stop-camera').style.display = 'inline-block';

        if (flashSupported) {
            document.getElementById('toggle-flash').style.display = 'inline-block';
        }

        showSuccess('{% trans "Camera started successfully" %}');
        console.log('Camera started successfully');

    } catch (error) {
        console.error('Camera error:', error);

        let errorMessage = '{% trans "Failed to access camera" %}';

        if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
            errorMessage = '{% trans "Camera permission denied. Please allow camera access and try again." %}';
        } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
            errorMessage = '{% trans "No camera found on this device." %}';
        } else if (error.name === 'NotSupportedError') {
            errorMessage = '{% trans "Camera not supported in this browser." %}';
        } else if (error.name === 'NotReadableError') {
            errorMessage = '{% trans "Camera is already in use by another application." %}';
        }

        showError(errorMessage);
    }
}

async function startBarcodeDetection() {
    try {
        // Wait for ZXing library to load
        if (typeof ZXing === 'undefined') {
            console.log('Waiting for ZXing library to load...');
            // Try again after a short delay
            setTimeout(() => {
                startBarcodeDetection();
            }, 500);
            return;
        }

        console.log('ZXing library loaded successfully');
        codeReader = new ZXing.BrowserMultiFormatReader();

        const video = document.getElementById('camera-feed');

        // Start continuous scanning
        codeReader.decodeFromVideoDevice(null, video, (result, error) => {
            if (result) {
                // Barcode detected!
                const barcodeText = result.getText();
                console.log('Barcode detected:', barcodeText);
                handleBarcodeDetection(barcodeText);
            }
            // Ignore errors as they're common during scanning
            if (error && !error.name.includes('NotFound')) {
                console.log('Scanner error (normal):', error.name);
            }
        });

        console.log('Barcode detection started successfully');
        showSuccess('{% trans "Camera and barcode detection ready" %}');

    } catch (error) {
        console.error('Barcode detection error:', error);
        showError('{% trans "Failed to start barcode detection" %}');
    }
}

function handleBarcodeDetection(barcodeText) {
    // Stop the continuous scanning to prevent multiple detections
    if (codeReader) {
        codeReader.reset();
    }

    // Fill the barcode input field
    document.getElementById('barcode-input').value = barcodeText;

    // Show success message
    showSuccess(`{% trans "Barcode detected:" %} ${barcodeText}`);

    // Auto-search the detected barcode
    setTimeout(() => {
        searchBarcode();
    }, 500);

    // Restart detection after a short delay
    setTimeout(() => {
        if (currentStream && document.getElementById('camera-section').classList.contains('active')) {
            startBarcodeDetection();
        }
    }, 2000);
}

function stopCamera() {
    // Stop barcode detection
    if (codeReader) {
        codeReader.reset();
        codeReader = null;
    }

    if (currentStream) {
        currentStream.getTracks().forEach(track => track.stop());
        currentStream = null;

        document.getElementById('start-camera').style.display = 'inline-block';
        document.getElementById('stop-camera').style.display = 'none';
        document.getElementById('toggle-flash').style.display = 'none';

        const video = document.getElementById('camera-feed');
        video.srcObject = null;
    }
}

async function toggleFlash() {
    if (currentStream && flashSupported) {
        const track = currentStream.getVideoTracks()[0];
        const constraints = track.getConstraints();

        try {
            await track.applyConstraints({
                advanced: [{
                    torch: !constraints.advanced?.[0]?.torch
                }]
            });
        } catch (error) {
            console.error('Flash toggle error:', error);
        }
    }
}
