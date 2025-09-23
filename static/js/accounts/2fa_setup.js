document.getElementById('verify2faForm').addEventListener('submit', function(e) {
    e.preventDefault();

    const formData = new FormData(this);
    const resultDiv = document.getElementById('verification-result');

    fetch('{% url "core:verify_2fa_setup" %}', {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            resultDiv.innerHTML = `
                <div class="alert alert-success">
                    <i class="fas fa-check-circle me-2"></i>
                    Two-factor authentication has been successfully enabled!
                </div>
            `;
            setTimeout(() => {
                window.location.href = data.redirect;
            }, 2000);
        } else {
            resultDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-times-circle me-2"></i>
                    ${data.error}
                </div>
            `;
        }
    })
    .catch(error => {
        resultDiv.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                An error occurred. Please try again.
            </div>
        `;
    });
});

function printBackupCodes() {
    const codes = [{% for code in backup_codes %}'{{ code }}'{% if not forloop.last %},{% endif %}{% endfor %}];

    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <html>
            <head>
                <title>2FA Backup Codes - ZAIN HMS</title>
                <style>
                    body { font-family: Arial, sans-serif; padding: 20px; }
                    .header { text-align: center; margin-bottom: 30px; }
                    .codes { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
                    .code { padding: 10px; border: 1px solid #ddd; font-family: monospace; }
                    .warning { background: #fff3cd; padding: 15px; border: 1px solid #ffeaa7; margin: 20px 0; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h2>Two-Factor Authentication Backup Codes</h2>
                    <p>ZAIN HMS - Unified Hospital Management System</p>
                    <p>User: {{ user.get_full_name|default:user.username }}</p>
                    <p>Generated: ${new Date().toLocaleString()}</p>
                </div>

                <div class="warning">
                    <strong>IMPORTANT:</strong> Store these codes in a secure location. Each code can only be used once.
                </div>

                <div class="codes">
                    ${codes.map(code => '<div class="code">' + code + '</div>').join('')}
                </div>
            </body>
        </html>
    `);
    printWindow.document.close();
    printWindow.print();
}

function downloadBackupCodes() {
    const codes = [{% for code in backup_codes %}'{{ code }}'{% if not forloop.last %},{% endif %}{% endfor %}];

    const content = `ZAIN HMS - Two-Factor Authentication Backup Codes
User: {{ user.get_full_name|default:user.username }}
Generated: ${new Date().toLocaleString()}

IMPORTANT: Store these codes securely. Each code can only be used once.

Backup Codes:
${codes.map((code, index) => (index + 1).toString().padStart(2, '0') + '. ' + code).join('\n')}

Keep these codes safe and secure!
`;

    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'zain_hms_2fa_backup_codes.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}
