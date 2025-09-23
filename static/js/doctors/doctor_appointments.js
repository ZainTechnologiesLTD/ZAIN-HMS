// Auto-submit form when status or date changes
document.getElementById('status').addEventListener('change', function() {
    this.form.submit();
});

document.getElementById('date_from').addEventListener('change', function() {
    if(this.value) {
        this.form.submit();
    }
});

document.getElementById('date_to').addEventListener('change', function() {
    if(this.value) {
        this.form.submit();
    }
});

// Add confirmation for actions
document.querySelectorAll('[title="Create Prescription"]').forEach(function(button) {
    button.addEventListener('click', function(e) {
        if (!confirm('Create a prescription for this appointment?')) {
            e.preventDefault();
        }
    });
});
