// Consolidated Patient Print JavaScript
// Includes all printing functionality for patient records

// Auto-print functionality (optional)
document.addEventListener('DOMContentLoaded', function() {
    // Uncomment the line below to auto-print when page loads
    // setTimeout(() => window.print(), 1000);

    // Optional: Auto-print when page loads (uncomment if desired)
    // setTimeout(() => window.print(), 500);
});

// Handle print event
window.addEventListener('beforeprint', function() {
    console.log('Preparing document for printing...');
    // Set document title for printing
    const patientName = document.querySelector('.patient-name, h1')?.textContent?.trim();
    if (patientName) {
        document.title = `Patient Record - ${patientName}`;
    }
});

window.addEventListener('afterprint', function() {
    console.log('Document printed successfully');
});

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    if (e.ctrlKey && e.key === 'p') {
        e.preventDefault();
        window.print();
    }
    if (e.key === 'Escape') {
        window.close();
    }
});

// Print button functionality
function printPatientRecord() {
    window.print();
}

// Print specific sections
function printSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        const printContent = section.innerHTML;
        const originalContent = document.body.innerHTML;

        document.body.innerHTML = printContent;
        window.print();
        document.body.innerHTML = originalContent;

        // Reload the page to restore full functionality
        window.location.reload();
    }
}
