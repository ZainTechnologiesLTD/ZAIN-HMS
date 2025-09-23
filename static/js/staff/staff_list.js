document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const roleFilter = document.getElementById('roleFilter');
    const statusFilter = document.getElementById('statusFilter');
    const clearFiltersBtn = document.getElementById('clearFilters');
    const tableRows = document.querySelectorAll('#staffTable tbody tr');

    function filterTable() {
        const searchTerm = searchInput.value.toLowerCase();
        const selectedRole = roleFilter.value;
        const selectedStatus = statusFilter.value;

        tableRows.forEach(row => {
            if (row.cells.length === 1) return; // Skip empty state row

            const name = row.cells[1].textContent.toLowerCase();
            const position = row.cells[2].textContent.toLowerCase();
            const email = row.cells[4].textContent.toLowerCase();
            const role = row.getAttribute('data-role') || '';
            const status = row.getAttribute('data-status');

            const matchesSearch = searchTerm === '' ||
                                name.includes(searchTerm) ||
                                position.includes(searchTerm) ||
                                email.includes(searchTerm);

            const matchesRole = selectedRole === '' || role === selectedRole;
            const matchesStatus = selectedStatus === '' || status === selectedStatus;

            if (matchesSearch && matchesRole && matchesStatus) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }

    searchInput.addEventListener('input', filterTable);
    roleFilter.addEventListener('change', filterTable);
    statusFilter.addEventListener('change', filterTable);

    clearFiltersBtn.addEventListener('click', function() {
        searchInput.value = '';
        roleFilter.value = '';
        statusFilter.value = '';
        filterTable();
    });

    // Copy to clipboard function
    window.copyToClipboard = function(text) {
        navigator.clipboard.writeText(text).then(function() {
            // Show success toast
            const toast = document.createElement('div');
            toast.className = 'toast-container position-fixed top-0 end-0 p-3';
            toast.innerHTML = `
                <div class="toast show" role="alert" aria-live="assertive" aria-atomic="true">
                    <div class="toast-body bg-success text-white rounded">
                        <i class="fas fa-check me-2"></i>Staff ID copied to clipboard!
                    </div>
                </div>
            `;
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 3000);
        }, function(err) {
            console.error('Could not copy text: ', err);
        });
    }
});
