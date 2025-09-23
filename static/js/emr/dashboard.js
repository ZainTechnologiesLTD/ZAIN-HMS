// Notification system for calculators
function showNotification(message, type = 'info', duration = 5000) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);';

    notification.innerHTML = `
        <i class="fas fa-${type === 'error' ? 'exclamation-triangle' : type === 'success' ? 'check-circle' : 'info-circle'} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    // Add to page
    document.body.appendChild(notification);

    // Auto-remove after duration
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, duration);
}

// Medical Calculator Functions
function showBMICalculator() {
    const result = prompt(`BMI Calculator\n\nEnter weight (kg) and height (m) separated by comma:\nExample: 70,1.75`);
    if (result) {
        const [weight, height] = result.split(',').map(x => parseFloat(x.trim()));
        if (weight && height) {
            const bmi = (weight / (height * height)).toFixed(1);
            let category = '';
            if (bmi < 18.5) category = 'Underweight';
            else if (bmi < 25) category = 'Normal';
            else if (bmi < 30) category = 'Overweight';
            else category = 'Obese';

            showNotification(`BMI: ${bmi} (${category})`, 'info', 8000);
        } else {
            showNotification('Invalid input. Please enter valid numbers.', 'error');
        }
    }
}

function showDoseCalculator() {
    const result = prompt(`Pediatric Dose Calculator\n\nEnter weight (kg) and adult dose (mg) separated by comma:\nExample: 25,500`);
    if (result) {
        const [weight, adultDose] = result.split(',').map(x => parseFloat(x.trim()));
        if (weight && adultDose) {
            const pediatricDose = ((weight / 70) * adultDose).toFixed(1);
            showNotification(`Pediatric Dose: ${pediatricDose} mg`, 'success', 8000);
        } else {
            showNotification('Invalid input. Please enter valid numbers.', 'error');
        }
    }
}

function showAgeCalculator() {
    const birthDate = prompt(`Age Calculator\n\nEnter birth date (YYYY-MM-DD):\nExample: 1990-05-15`);
    if (birthDate) {
        const birth = new Date(birthDate);
        const today = new Date();
        if (!isNaN(birth)) {
            const ageMs = today - birth;
            const years = Math.floor(ageMs / (365.25 * 24 * 60 * 60 * 1000));
            const months = Math.floor((ageMs % (365.25 * 24 * 60 * 60 * 1000)) / (30.44 * 24 * 60 * 60 * 1000));
            showNotification(`Age: ${years} years, ${months} months`, 'info', 8000);
        } else {
            showNotification('Invalid date format. Use YYYY-MM-DD.', 'error');
        }
    }
}

function showGFRCalculator() {
    const result = prompt(`eGFR Calculator (CKD-EPI)\n\nEnter creatinine (mg/dL), age, and gender (M/F) separated by commas:\nExample: 1.2,45,M`);
    if (result) {
        const [creat, age, gender] = result.split(',').map(x => x.trim());
        const creatinine = parseFloat(creat);
        const ageNum = parseInt(age);

        if (creatinine && ageNum && (gender === 'M' || gender === 'F')) {
            let gfr;
            if (gender === 'F') {
                gfr = creatinine <= 0.7 ? 144 * Math.pow(creatinine/0.7, -0.329) * Math.pow(0.993, ageNum) :
                      144 * Math.pow(creatinine/0.7, -1.209) * Math.pow(0.993, ageNum);
            } else {
                gfr = creatinine <= 0.9 ? 141 * Math.pow(creatinine/0.9, -0.411) * Math.pow(0.993, ageNum) :
                      141 * Math.pow(creatinine/0.9, -1.209) * Math.pow(0.993, ageNum);
            }
            showNotification(`eGFR: ${gfr.toFixed(0)} mL/min/1.73m²`, 'info', 8000);
        } else {
            showNotification('Invalid input. Check format: creatinine,age,M/F', 'error');
        }
    }
}
