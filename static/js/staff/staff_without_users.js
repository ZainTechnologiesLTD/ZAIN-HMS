document.addEventListener('DOMContentLoaded', function() {
    const selectAllCheckbox = document.getElementById('selectAll');
    const staffCheckboxes = document.querySelectorAll('.staff-checkbox');
    const bulkCreateButton = document.getElementById('bulkCreateSelected');
    const selectedCountSpan = document.getElementById('selectedCount');

    function updateSelectedCount() {
        const checkedBoxes = document.querySelectorAll('.staff-checkbox:checked');
        const count = checkedBoxes.length;

        selectedCountSpan.textContent = `${count} selected`;
        bulkCreateButton.disabled = count === 0;

        // Update select all checkbox state
        if (count === 0) {
            selectAllCheckbox.indeterminate = false;
            selectAllCheckbox.checked = false;
        } else if (count === staffCheckboxes.length) {
            selectAllCheckbox.indeterminate = false;
            selectAllCheckbox.checked = true;
        } else {
            selectAllCheckbox.indeterminate = true;
        }
    }

    // Select all functionality
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            staffCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateSelectedCount();
        });
    }

    // Individual checkbox change
    staffCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateSelectedCount);
    });

    // Bulk create selected
    if (bulkCreateButton) {
        bulkCreateButton.addEventListener('click', function() {
            const checkedBoxes = document.querySelectorAll('.staff-checkbox:checked');
            const selectedIds = Array.from(checkedBoxes).map(cb => cb.value);

            if (selectedIds.length === 0) return;

            // Update modal content
            document.getElementById('selectedCountModal').textContent = selectedIds.length;
            document.getElementById('selectedPlural').style.display = selectedIds.length === 1 ? 'none' : 'inline';
            document.getElementById('selectedStaffInput').value = selectedIds.join(',');

            // Show staff list in modal
            const staffListDiv = document.getElementById('selectedStaffList');
            let staffListHtml = '<div class="alert alert-info"><h6>Selected staff:</h6><ul class="mb-0">';

            checkedBoxes.forEach(checkbox => {
                const row = checkbox.closest('tr');
                const name = row.querySelector('td:nth-child(3) .fw-semibold').textContent;
                const position = row.querySelector('td:nth-child(4) .badge').textContent;
                staffListHtml += `<li>${name} (${position})</li>`;
            });

            staffListHtml += '</ul></div>';
            staffListDiv.innerHTML = staffListHtml;

            // Show modal
            new bootstrap.Modal(document.getElementById('bulkCreateSelectedModal')).show();
        });
    }

    // Initialize count
    updateSelectedCount();
});
