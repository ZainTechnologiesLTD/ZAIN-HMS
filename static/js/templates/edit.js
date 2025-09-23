// Show/hide subject field based on channel selection
document.getElementById('channel').addEventListener('change', function() {
    const subjectField = document.getElementById('subject-field');
    if (this.value === 'email') {
        subjectField.style.display = 'block';
        document.getElementById('subject_template').required = true;
    } else {
        subjectField.style.display = 'none';
        document.getElementById('subject_template').required = false;
    }
});
