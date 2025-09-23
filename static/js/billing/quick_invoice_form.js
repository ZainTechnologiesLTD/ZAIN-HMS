    // Initialize Select2 for better multiple select experience
    $(document).ready(function() {
        $('#appointments').select2({
            placeholder: 'Select appointments',
            width: '100%'
        });
        $('#lab_tests').select2({
            placeholder: 'Select lab tests',
            width: '100%'
        });
    });
