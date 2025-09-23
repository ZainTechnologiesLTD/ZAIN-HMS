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
