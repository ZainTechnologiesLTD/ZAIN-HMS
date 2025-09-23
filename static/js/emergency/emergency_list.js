    document.addEventListener('DOMContentLoaded', function() {
        // Initialize Select2
        $('#priorityFilter, #statusFilter').select2({
            minimumResultsForSearch: Infinity
        });

        // Filter handling
        function updateFilters() {
            const priority = $('#priorityFilter').val();
            const status = $('#statusFilter').val();

            htmx.ajax('GET', '{% url "emergency:cases_filter" %}', {
                target: '#casesContainer',
                values: {
                    priority: priority,
                    status: status
                }
            });
        }

        $('#priorityFilter, #statusFilter').on('change', updateFilters);

        // Toast notifications
        htmx.on('showMessage', (e) => {
            toastr.success(e.detail.message);
        });
    });
