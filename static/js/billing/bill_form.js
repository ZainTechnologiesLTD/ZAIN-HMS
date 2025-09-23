document.addEventListener('DOMContentLoaded', function() {
    console.log('Bill form script loaded');

    // Auto-populate due date when invoice date changes
    const invoiceDateField = document.querySelector('input[name="invoice_date"]');
    const dueDateField = document.querySelector('input[name="due_date"]');
    const paymentTermsField = document.querySelector('select[name="payment_terms"]');
    const form = document.querySelector('form');
    const submitButton = document.querySelector('button[type="submit"]');

    console.log('Form elements found:', {
        form: !!form,
        submitButton: !!submitButton,
        invoiceDateField: !!invoiceDateField,
        dueDateField: !!dueDateField,
        paymentTermsField: !!paymentTermsField
    });

    // Add form submit event listener
    if (form) {
        form.addEventListener('submit', function(e) {
            console.log('Form submit event triggered');
            console.log('Form data:', new FormData(form));
        });
    }

    // Add button click event listener
    if (submitButton) {
        submitButton.addEventListener('click', function(e) {
            console.log('Submit button clicked');
        });
    }

    function updateDueDate() {
        if (invoiceDateField.value && paymentTermsField.value) {
            const invoiceDate = new Date(invoiceDateField.value);
            let daysToAdd = 0;

            switch(paymentTermsField.value) {
                case 'IMMEDIATE':
                    daysToAdd = 0;
                    break;
                case 'NET_15':
                    daysToAdd = 15;
                    break;
                case 'NET_30':
                    daysToAdd = 30;
                    break;
            }

            const dueDate = new Date(invoiceDate);
            dueDate.setDate(dueDate.getDate() + daysToAdd);

            dueDateField.value = dueDate.toISOString().split('T')[0];
        }
    }

    if (invoiceDateField) {
        invoiceDateField.addEventListener('change', updateDueDate);
    }
    if (paymentTermsField) {
        paymentTermsField.addEventListener('change', updateDueDate);
    }
});
