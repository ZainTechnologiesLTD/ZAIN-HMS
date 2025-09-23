// User account management
function unlinkUser(doctorId) {
    if (confirm('Are you sure you want to unlink this user account from the doctor? The user account will remain but will no longer be associated with this doctor.')) {
        fetch(`/doctors/${doctorId}/unlink-user/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/x-www-form-urlencoded',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(data.message);
                location.reload();
            } else {
                alert('Error: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while unlinking the user.');
        });
    }
}

// Create user account confirmation
document.addEventListener('DOMContentLoaded', function() {
    const createUserForm = document.querySelector('.create-user-form');
    if (createUserForm) {
        createUserForm.addEventListener('submit', function(e) {
            if (!confirm('Create a user account for this doctor? An email with login credentials will be sent to their email address.')) {
                e.preventDefault();
            }
        });
    }
});
