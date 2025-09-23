$(document).ready(function() {
    // Add search functionality with auto-submit delay
    let searchTimeout;
    $('input[name="search"]').on('input', function() {
        clearTimeout(searchTimeout);
        const form = $(this).closest('form');
        searchTimeout = setTimeout(function() {
            // Auto-submit after 1 second of no typing
        }, 1000);
    });
});
