function togglePassword(fieldId) {
    const field = document.getElementById(fieldId);
    const icon = document.getElementById(fieldId + '_icon');

    if (field.type === 'password') {
        field.type = 'text';
        icon.className = 'bi bi-eye-slash';
    } else {
        field.type = 'password';
        icon.className = 'bi bi-eye';
    }
}

function checkPasswordStrength(password) {
    const strengthBar = document.getElementById('strength-bar');
    const strengthText = document.getElementById('strength-text');

    let strength = 0;
    let text = '';
    let className = '';

    if (password.length >= 8) strength++;
    if (/[a-z]/.test(password)) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^A-Za-z0-9]/.test(password)) strength++;

    switch (strength) {
        case 0:
        case 1:
            text = 'Very Weak';
            className = 'strength-weak';
            strengthBar.style.width = '20%';
            break;
        case 2:
            text = 'Weak';
            className = 'strength-weak';
            strengthBar.style.width = '40%';
            break;
        case 3:
            text = 'Medium';
            className = 'strength-medium';
            strengthBar.style.width = '60%';
            break;
        case 4:
            text = 'Strong';
            className = 'strength-strong';
            strengthBar.style.width = '80%';
            break;
        case 5:
            text = 'Very Strong';
            className = 'strength-strong';
            strengthBar.style.width = '100%';
            break;
    }

    strengthBar.className = 'password-strength ' + className;
    strengthText.textContent = text;
    strengthText.className = 'small text-' + (strength <= 2 ? 'danger' : strength === 3 ? 'warning' : 'success');
}

function checkPasswordMatch() {
    const password1 = document.getElementById('{{ form.new_password1.id_for_label }}').value;
    const password2 = document.getElementById('{{ form.new_password2.id_for_label }}').value;
    const matchDiv = document.getElementById('password-match');

    if (password2.length > 0) {
        if (password1 === password2) {
            matchDiv.innerHTML = '<small class="text-success"><i class="bi bi-check-circle me-1"></i>Passwords match</small>';
        } else {
            matchDiv.innerHTML = '<small class="text-danger"><i class="bi bi-x-circle me-1"></i>Passwords do not match</small>';
        }
    } else {
        matchDiv.innerHTML = '';
    }
}
