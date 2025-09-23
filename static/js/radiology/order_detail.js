function updateStatus(newStatus) {
    if (confirm(`Are you sure you want to change the order status to ${newStatus.replace('_', ' ')}?`)) {
        // Create a form and submit it
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = window.location.href;

        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = csrfToken;

        const statusInput = document.createElement('input');
        statusInput.type = 'hidden';
        statusInput.name = 'status';
        statusInput.value = newStatus;

        form.appendChild(csrfInput);
        form.appendChild(statusInput);
        document.body.appendChild(form);
        form.submit();
    }
}
