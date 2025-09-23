    function billingManager() {
        return {
            currentView: 'grid',

            init() {
                this.setupEventListeners();
                this.setupViewToggle();
            },

            setupEventListeners() {
                // Bill card click handling
                document.addEventListener('click', (e) => {
                    const billCard = e.target.closest('.bill-card, .bill-list-item');
                    if (billCard && !e.target.closest('.btn, .dropdown, .payment-method')) {
                        const billId = billCard.dataset.billId;
                        window.location.href = `/billing/${billId}/`;
                    }
                });
            },

            setupViewToggle() {
                document.querySelectorAll('input[name="viewMode"]').forEach(input => {
                    input.addEventListener('change', (e) => {
                        this.switchView(e.target.id.replace('View', ''));
                    });
                });
            },

            switchView(viewType) {
                this.currentView = viewType;

                // Hide all views
                document.querySelectorAll('#gridViewContent, #listViewContent').forEach(view => {
                    view.classList.add('d-none');
                });

                // Show selected view
                document.getElementById(viewType + 'ViewContent').classList.remove('d-none');
            }
        }
    }

    function recordPayment(billId, method = null) {
        document.getElementById('billId').value = billId;

        if (method) {
            document.querySelector('select[name="payment_method"]').value = method;
        }

        // Get bill amount and set as default
        fetch(`/billing/api/bill/${billId}/`)
            .then(response => response.json())
            .then(data => {
                document.querySelector('input[name="amount"]').value = data.total_amount;
            });

        new bootstrap.Modal(document.getElementById('paymentModal')).show();
    }

    function submitPayment() {
        const form = document.getElementById('paymentForm');
        const formData = new FormData(form);

        fetch('/billing/api/record-payment/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                bootstrap.Modal.getInstance(document.getElementById('paymentModal')).hide();
                showNotification('Payment recorded successfully!', 'success');
                location.reload();
            } else {
                showNotification('Failed to record payment: ' + data.error, 'error');
            }
        });
    }

    function cancelBill(billId) {
        if (confirm('Are you sure you want to cancel this bill?')) {
            fetch(`/billing/api/cancel-bill/${billId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification('Bill cancelled successfully!', 'success');
                    location.reload();
                } else {
                    showNotification('Failed to cancel bill', 'error');
                }
            });
        }
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Real-time updates
    document.addEventListener('DOMContentLoaded', function() {
        // Refresh billing data every 2 minutes
        setInterval(() => {
            htmx.trigger('#billsList', 'refresh');
        }, 120000);

        // Initialize tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
{% block extra_js %}
<script src="{% static 'js/enhanced-common.js' %}">

    document.addEventListener('DOMContentLoaded', function() {
        // Initialize billing functionality
        if (typeof initBilling === 'function') {
            initBilling();
        }
    });
