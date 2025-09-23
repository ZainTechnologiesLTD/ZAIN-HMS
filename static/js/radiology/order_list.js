function updateOrderStatus(orderId, newStatus) {
    const modal = new bootstrap.Modal(document.getElementById('statusUpdateModal'));

    document.getElementById('confirmStatusUpdate').onclick = function() {
        // You can implement AJAX call here or create a form submission
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/radiology/orders/${orderId}/update-status/`;

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
    };

    modal.show();
}

// Auto-submit forms on filter change
document.addEventListener('DOMContentLoaded', function() {
    const filterSelects = document.querySelectorAll('select[name="status"], select[name="priority"]');
    filterSelects.forEach(select => {
        select.addEventListener('change', function() {
            this.form.submit();
        });
    });
});
