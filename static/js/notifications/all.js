document.addEventListener('DOMContentLoaded', function() {
    // Update current time every minute
    function updateTime() {
        const now = new Date();
        const timeString = now.toLocaleString('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
        });
        const timeElement = document.getElementById('current-time');
        if (timeElement) {
            timeElement.textContent = timeString;
        }
    }

    setInterval(updateTime, 60000); // Update every minute
});
