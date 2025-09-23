// Auto-redirect to dashboard after 5 seconds
setTimeout(function() {
    window.location.href = "{% url 'core:home' %}";
}, 5000);
