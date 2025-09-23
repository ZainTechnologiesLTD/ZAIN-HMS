function markAsRead(notificationId) {
    fetch(`/core/notifications/${notificationId}/read/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            location.reload();
        }
    })
    .catch(error => console.error('Error:', error));
}

// Auto refresh dashboard every 5 minutes
setTimeout(() => {
    location.reload();
}, 300000);
