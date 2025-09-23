    // Auto-submit form when filters change
    document.addEventListener('DOMContentLoaded', function() {
        const filters = ['department', 'shift'];
        filters.forEach(filterId => {
            const filterElement = document.getElementById(filterId);
            if (filterElement) {
                filterElement.addEventListener('change', function() {
                    this.form.submit();
                });
            }
        });
    });

    // Copy to clipboard function
    function copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(function() {
            // Show success toast
            const toast = document.createElement('div');
            toast.className = 'toast-container position-fixed top-0 end-0 p-3';
            toast.innerHTML = `
                <div class="toast show" role="alert" aria-live="assertive" aria-atomic="true">
                    <div class="toast-body bg-success text-white rounded">
                        <i class="fas fa-check me-2"></i>Employee ID copied to clipboard!
                    </div>
                </div>
            `;
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 3000);
        }, function(err) {
            console.error('Could not copy text: ', err);
        });
    }
