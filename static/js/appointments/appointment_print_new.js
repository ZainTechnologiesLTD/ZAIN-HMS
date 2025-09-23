        // Simple print functionality
        document.addEventListener('DOMContentLoaded', function() {
            // Auto-print if requested
            if (window.location.search.includes('auto_print=true')) {
                setTimeout(() => window.print(), 500);
            }

            // Print event handlers
            window.addEventListener('beforeprint', function() {
                document.querySelectorAll('.print-actions').forEach(el => {
                    el.style.display = 'none';
                });
            });

            window.addEventListener('afterprint', function() {
                document.querySelectorAll('.print-actions').forEach(el => {
                    el.style.display = 'flex';
                });
            });

            // Keyboard shortcut for print
            document.addEventListener('keydown', function(event) {
                if ((event.ctrlKey || event.metaKey) && event.key === 'p') {
                    event.preventDefault();
                    window.print();
                }
            });
        });
