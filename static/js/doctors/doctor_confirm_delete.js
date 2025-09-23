document.addEventListener('DOMContentLoaded', function() {
    const confirmNameInput = document.getElementById('confirmName');
    const deleteBtn = document.getElementById('deleteBtn');
    const expectedName = "{{ doctor.get_full_name }}";

    confirmNameInput.addEventListener('input', function() {
        if (this.value.trim() === expectedName) {
            deleteBtn.disabled = false;
            deleteBtn.classList.add('btn-danger');
        } else {
            deleteBtn.disabled = true;
        }
    });

    // Prevent accidental form submission
    document.querySelector('form').addEventListener('submit', function(e) {
        if (confirmNameInput.value.trim() !== expectedName) {
            e.preventDefault();
            alert('Please type the exact doctor name to confirm deletion.');
            return false;
        }

        // Final confirmation
        if (!confirm('Are you absolutely sure you want to delete this doctor? This action cannot be undone.')) {
            e.preventDefault();
            return false;
        }
    });
});
