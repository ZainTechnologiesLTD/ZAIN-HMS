$(document).ready(function() {
    // Auto-refresh page every 30 seconds for real-time updates
    setInterval(function() {
        // Only refresh if user is not actively interacting
        if (document.hidden === false) {
            location.reload();
        }
    }, 30000);
});
