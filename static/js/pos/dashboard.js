// Auto refresh dashboard every 5 minutes
setTimeout(function() {
    location.reload();
}, 300000);

// Add some interactivity
document.addEventListener('DOMContentLoaded', function() {
    // Add hover effects to action buttons
    const actionBtns = document.querySelectorAll('.pos-action-btn');
    actionBtns.forEach(btn => {
        btn.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });
        btn.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
});
