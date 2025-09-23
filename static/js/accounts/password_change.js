document.addEventListener('DOMContentLoaded', function() {
    const newPasswordField = document.getElementById('{{ form.new_password.id_for_label }}');
    const confirmPasswordField = document.getElementById('{{ form.confirm_password.id_for_label }}');
    const lengthReq = document.getElementById('length-req');
    const matchReq = document.getElementById('match-req');

    function updateRequirements() {
        const password = newPasswordField.value;
        const confirmPassword = confirmPasswordField.value;

        // Check length requirement
        if (password.length >= 8) {
            lengthReq.querySelector('i').className = 'fas fa-check valid';
            lengthReq.classList.add('valid');
            lengthReq.classList.remove('invalid');
        } else {
            lengthReq.querySelector('i').className = 'fas fa-times invalid';
            lengthReq.classList.add('invalid');
            lengthReq.classList.remove('valid');
        }

        // Check match requirement
        if (password && confirmPassword && password === confirmPassword) {
            matchReq.querySelector('i').className = 'fas fa-check valid';
            matchReq.classList.add('valid');
            matchReq.classList.remove('invalid');
        } else {
            matchReq.querySelector('i').className = 'fas fa-times invalid';
            matchReq.classList.add('invalid');
            matchReq.classList.remove('valid');
        }
    }

    newPasswordField.addEventListener('input', updateRequirements);
    confirmPasswordField.addEventListener('input', updateRequirements);

    // Form validation
    document.getElementById('passwordChangeForm').addEventListener('submit', function(e) {
        const password = newPasswordField.value;
        const confirmPassword = confirmPasswordField.value;

        if (password.length < 8) {
            e.preventDefault();
            alert('Password must be at least 8 characters long.');
            return false;
        }

        if (password !== confirmPassword) {
            e.preventDefault();
            alert('Passwords do not match.');
            return false;
        }
    });
});
