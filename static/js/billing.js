/* ZAIN HMS - Billing Module JavaScript */

// Billing Manager
function initBilling() {
    console.log('Billing module initialized');
    
    // Setup billing functionality
    setupBillFilters();
    setupPaymentMethods();
    setupBillActions();
    setupExportFunctions();
}

function setupBillFilters() {
    const filterForm = document.querySelector('.bill-filters form');
    if (filterForm) {
        filterForm.addEventListener('submit', function(e) {
            // Add loading state
            const submitBtn = this.querySelector('[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Filtering...';
            }
        });
    }
}

function setupPaymentMethods() {
    const paymentMethods = document.querySelectorAll('.payment-method-card');
    paymentMethods.forEach(method => {
        method.addEventListener('click', function() {
            // Remove selected from all
            paymentMethods.forEach(m => m.classList.remove('selected'));
            // Add selected to clicked
            this.classList.add('selected');
        });
    });
}

function setupBillActions() {
    // View bill details
    document.querySelectorAll('[data-action="view-bill"]').forEach(btn => {
        btn.addEventListener('click', function() {
            const billId = this.dataset.billId;
            viewBillDetails(billId);
        });
    });
    
    // Print bill
    document.querySelectorAll('[data-action="print-bill"]').forEach(btn => {
        btn.addEventListener('click', function() {
            const billId = this.dataset.billId;
            printBill(billId);
        });
    });
    
    // Record payment
    document.querySelectorAll('[data-action="record-payment"]').forEach(btn => {
        btn.addEventListener('click', function() {
            const billId = this.dataset.billId;
            recordPayment(billId);
        });
    });
}

function setupExportFunctions() {
    // Export reports
    document.querySelectorAll('[data-action="export"]').forEach(btn => {
        btn.addEventListener('click', function() {
            const format = this.dataset.format || 'pdf';
            exportBillingReport(format);
        });
    });
}

// Bill Functions
function viewBillDetails(billId) {
    // Show bill details modal or navigate to detail page
    console.log('Viewing bill details for:', billId);
    // Implementation depends on your UI framework
}

function printBill(billId) {
    // Open print dialog for specific bill
    const printUrl = `/billing/bills/${billId}/print/`;
    window.open(printUrl, '_blank');
}

function recordPayment(billId, method = null) {
    console.log('Recording payment for bill:', billId, 'Method:', method);
    
    // Show payment recording modal or form
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Record Payment</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <form id="payment-form">
                        <input type="hidden" name="bill_id" value="${billId}">
                        <div class="mb-3">
                            <label class="form-label">Payment Method</label>
                            <select class="form-select" name="payment_method" required>
                                <option value="">Select method...</option>
                                <option value="CASH" ${method === 'CASH' ? 'selected' : ''}>Cash</option>
                                <option value="CARD" ${method === 'CARD' ? 'selected' : ''}>Card</option>
                                <option value="INSURANCE" ${method === 'INSURANCE' ? 'selected' : ''}>Insurance</option>
                                <option value="BANK_TRANSFER" ${method === 'BANK_TRANSFER' ? 'selected' : ''}>Bank Transfer</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Amount</label>
                            <input type="number" class="form-control" name="amount" step="0.01" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Reference</label>
                            <input type="text" class="form-control" name="reference" placeholder="Transaction reference">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Notes</label>
                            <textarea class="form-control" name="notes" rows="3"></textarea>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-primary" onclick="submitPayment()">Record Payment</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    // Clean up when modal is hidden
    modal.addEventListener('hidden.bs.modal', function() {
        document.body.removeChild(modal);
    });
}

function submitPayment() {
    const form = document.getElementById('payment-form');
    const formData = new FormData(form);
    
    // Add CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    if (csrfToken) {
        formData.append('csrfmiddlewaretoken', csrfToken);
    }
    
    fetch('/billing/record-payment/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Payment recorded successfully', 'success');
            location.reload(); // Refresh the page to show updated status
        } else {
            showNotification(data.message || 'Failed to record payment', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred while recording payment', 'error');
    });
}

function cancelBill(billId) {
    if (confirm('Are you sure you want to cancel this bill? This action cannot be undone.')) {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        
        fetch(`/billing/bills/${billId}/cancel/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Bill cancelled successfully', 'success');
                location.reload();
            } else {
                showNotification(data.message || 'Failed to cancel bill', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('An error occurred while cancelling bill', 'error');
        });
    }
}

function exportBillingReport(format = 'pdf') {
    const params = new URLSearchParams(window.location.search);
    params.set('format', format);
    
    const exportUrl = `/billing/export/?${params.toString()}`;
    window.open(exportUrl, '_blank');
}

// Bill Status Management
function updateBillStatus(billId, newStatus) {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    
    fetch(`/billing/bills/${billId}/update-status/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: newStatus })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Bill status updated successfully', 'success');
            location.reload();
        } else {
            showNotification(data.message || 'Failed to update bill status', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred while updating bill status', 'error');
    });
}

// Search and Filter Functions
function searchBills(query) {
    const billCards = document.querySelectorAll('.bill-card');
    const searchTerm = query.toLowerCase();
    
    billCards.forEach(card => {
        const billNumber = card.querySelector('.bill-number')?.textContent.toLowerCase() || '';
        const patientName = card.querySelector('.bill-patient')?.textContent.toLowerCase() || '';
        const shouldShow = billNumber.includes(searchTerm) || patientName.includes(searchTerm);
        
        card.style.display = shouldShow ? 'block' : 'none';
    });
}

// Real-time updates for billing status
function setupRealTimeUpdates() {
    setInterval(() => {
        updateBillStatuses();
    }, 30000); // Update every 30 seconds
}

function updateBillStatuses() {
    const billCards = document.querySelectorAll('.bill-card[data-bill-id]');
    const billIds = Array.from(billCards).map(card => card.dataset.billId);
    
    if (billIds.length > 0) {
        fetch('/billing/api/bill-statuses/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value
            },
            body: JSON.stringify({ bill_ids: billIds })
        })
        .then(response => response.json())
        .then(data => {
            data.bills.forEach(bill => {
                updateBillCardStatus(bill.id, bill.status, bill.amount_paid);
            });
        })
        .catch(error => {
            console.error('Error updating bill statuses:', error);
        });
    }
}

function updateBillCardStatus(billId, status, amountPaid) {
    const billCard = document.querySelector(`[data-bill-id="${billId}"]`);
    if (billCard) {
        const statusElement = billCard.querySelector('.bill-status');
        if (statusElement) {
            statusElement.textContent = status;
            statusElement.className = `bill-status ${status.toLowerCase()}`;
        }
        
        const amountElement = billCard.querySelector('.amount-paid');
        if (amountElement) {
            amountElement.textContent = `$${amountPaid}`;
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initBilling();
    setupRealTimeUpdates();
});
