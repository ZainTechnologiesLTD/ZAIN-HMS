document.addEventListener('DOMContentLoaded', function() {
    const checkboxes = document.querySelectorAll('.test-checkbox');
    const selectedCountEl = document.getElementById('selected-count');
    const totalAmountEl = document.getElementById('total-amount');
    const submitBtn = document.getElementById('submitBtn');

    function updateSummary() {
        let selectedCount = 0;
        let totalAmount = 0;

        checkboxes.forEach(checkbox => {
            if (checkbox.checked) {
                selectedCount++;
                totalAmount += parseFloat(checkbox.dataset.price);
            }
        });

        selectedCountEl.textContent = selectedCount;
        totalAmountEl.textContent = '$' + totalAmount.toFixed(2);
        submitBtn.disabled = selectedCount === 0;
    }

    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateSummary);
    });
});
