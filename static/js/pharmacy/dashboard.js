$(document).ready(function() {
    // Auto-refresh dashboard data every 5 minutes
    setTimeout(function() {
        location.reload();
    }, 300000);

    // Add hover effects to metric cards
    $('.metric-card').hover(
        function() {
            $(this).css('transform', 'translateY(-5px)');
        },
        function() {
            $(this).css('transform', 'translateY(0)');
        }
    );
});
