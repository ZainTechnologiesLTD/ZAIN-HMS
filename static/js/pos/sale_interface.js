// PoS Sale Interface JavaScript
let cart = [];
let selectedCustomer = null;
let selectedPrescription = null;

// CSRF token
const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '{{ csrf_token }}';

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    updateCartDisplay();
});

function initializeEventListeners() {
    // Medicine search
    const medicineSearch = document.getElementById('medicine-search');
    let searchTimeout;
    medicineSearch.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            searchMedicines(this.value);
        }, 300);
    });

    // Customer search
    const customerSearch = document.getElementById('customer-search');
    let customerSearchTimeout;
    customerSearch.addEventListener('input', function() {
        clearTimeout(customerSearchTimeout);
        customerSearchTimeout = setTimeout(() => {
            searchCustomers(this.value);
        }, 300);
    });

    // Customer clear
    document.getElementById('customer-clear').addEventListener('click', function() {
        clearCustomer();
    });

    // Add to cart buttons
    document.addEventListener('click', function(e) {
        if (e.target.closest('.add-to-cart')) {
            const card = e.target.closest('.medicine-card');
            addToCart(card);
        }
    });

    // Discount calculation
    document.getElementById('discount-percentage').addEventListener('input', calculateTotals);
    document.getElementById('amount-paid').addEventListener('input', calculateChange);

    // Checkout
    document.getElementById('checkout-btn').addEventListener('click', processCheckout);

    // Load prescription
    document.addEventListener('click', function(e) {
        if (e.target.closest('.load-prescription')) {
            const prescriptionId = e.target.closest('.load-prescription').dataset.prescriptionId;
            loadPrescription(prescriptionId);
        }
    });
}

async function searchMedicines(query) {
    if (query.length < 2) {
        // Show initial medicines
        return;
    }

    try {
        const response = await fetch('{% url "pharmacy:api_search_medicines" %}', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ query: query })
        });

        const data = await response.json();
        displayMedicines(data.medicines);
    } catch (error) {
        console.error('Error searching medicines:', error);
    }
}

function displayMedicines(medicines) {
    const resultsContainer = document.getElementById('search-results');

    if (medicines.length === 0) {
        resultsContainer.innerHTML = `
            <div class="text-center py-4 text-muted">
                <i class="fas fa-search fa-2x mb-2"></i>
                <p>No medicines found</p>
            </div>
        `;
        return;
    }

    resultsContainer.innerHTML = medicines.map(medicine => `
        <div class="medicine-card" data-medicine-id="${medicine.id}"
             data-medicine-name="${medicine.name}"
             data-medicine-price="${medicine.price}"
             data-medicine-stock="${medicine.stock}"
             data-medicine-unit="${medicine.unit}">
            <div class="row align-items-center">
                <div class="col-md-6">
                    <h6 class="mb-1">${medicine.name}</h6>
                    <small class="text-muted">${medicine.generic_name} - ${medicine.strength}</small>
                </div>
                <div class="col-md-2 text-center">
                    <span class="badge bg-${medicine.stock > 10 ? 'success' : medicine.stock > 5 ? 'warning' : 'danger'}">
                        ${medicine.stock} ${medicine.unit}
                    </span>
                </div>
                <div class="col-md-2 text-center">
                    <strong>$${parseFloat(medicine.price).toFixed(2)}</strong>
                </div>
                <div class="col-md-2 text-center">
                    <button class="btn btn-sm btn-primary add-to-cart">
                        <i class="fas fa-plus"></i>
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

async function searchCustomers(query) {
    if (query.length < 2) return;

    try {
        const response = await fetch('{% url "pharmacy:api_search_patients" %}', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ query: query })
        });

        const data = await response.json();
        displayCustomers(data.patients);
    } catch (error) {
        console.error('Error searching customers:', error);
    }
}

function displayCustomers(patients) {
    // Create dropdown with patient suggestions
    let dropdown = document.getElementById('customer-dropdown');
    if (!dropdown) {
        dropdown = document.createElement('div');
        dropdown.id = 'customer-dropdown';
        dropdown.className = 'dropdown-menu show';
        dropdown.style.position = 'absolute';
        dropdown.style.top = '100%';
        dropdown.style.left = '0';
        dropdown.style.right = '0';
        dropdown.style.zIndex = '1000';
        document.getElementById('customer-search').parentElement.style.position = 'relative';
        document.getElementById('customer-search').parentElement.appendChild(dropdown);
    }

    if (patients.length === 0) {
        dropdown.innerHTML = '<div class="dropdown-item-text">No patients found</div>';
        return;
    }

    dropdown.innerHTML = patients.map(patient => `
        <a class="dropdown-item customer-option" href="#"
           data-customer-id="${patient.id}"
           data-customer-name="${patient.name}"
           data-customer-phone="${patient.phone}">
            <strong>${patient.name}</strong><br>
            <small class="text-muted">${patient.phone}</small>
        </a>
    `).join('');

    // Add click handlers
    dropdown.querySelectorAll('.customer-option').forEach(option => {
        option.addEventListener('click', function(e) {
            e.preventDefault();
            selectCustomer({
                id: this.dataset.customerId,
                name: this.dataset.customerName,
                phone: this.dataset.customerPhone
            });
            dropdown.remove();
        });
    });
}

function selectCustomer(customer) {
    selectedCustomer = customer;
    document.getElementById('customer-search').value = customer.name;
    document.getElementById('customer-name').textContent = customer.name;
    document.getElementById('customer-phone').textContent = customer.phone;
    document.getElementById('selected-customer').classList.remove('d-none');
    document.getElementById('walk-in-customer').style.display = 'none';
}

function clearCustomer() {
    selectedCustomer = null;
    document.getElementById('customer-search').value = '';
    document.getElementById('selected-customer').classList.add('d-none');
    document.getElementById('walk-in-customer').style.display = 'block';
}

function addToCart(medicineCard) {
    const medicineId = medicineCard.dataset.medicineId;
    const medicineName = medicineCard.dataset.medicineName;
    const medicinePrice = parseFloat(medicineCard.dataset.medicinePrice);
    const medicineStock = parseInt(medicineCard.dataset.medicineStock);
    const medicineUnit = medicineCard.dataset.medicineUnit;

    // Check if already in cart
    const existingItem = cart.find(item => item.id === medicineId);
    if (existingItem) {
        if (existingItem.quantity < medicineStock) {
            existingItem.quantity += 1;
        } else {
            alert('Cannot add more. Stock limit reached.');
            return;
        }
    } else {
        cart.push({
            id: medicineId,
            name: medicineName,
            price: medicinePrice,
            quantity: 1,
            stock: medicineStock,
            unit: medicineUnit
        });
    }

    updateCartDisplay();
    calculateTotals();
}

function updateCartDisplay() {
    const cartContainer = document.getElementById('cart-container');
    const emptyCart = document.getElementById('empty-cart');

    if (cart.length === 0) {
        emptyCart.style.display = 'block';
        cartContainer.querySelector('.cart-items-list')?.remove();
        document.getElementById('checkout-btn').disabled = true;
        return;
    }

    emptyCart.style.display = 'none';
    document.getElementById('checkout-btn').disabled = false;

    let cartItemsList = cartContainer.querySelector('.cart-items-list');
    if (!cartItemsList) {
        cartItemsList = document.createElement('div');
        cartItemsList.className = 'cart-items-list';
        cartContainer.appendChild(cartItemsList);
    }

    cartItemsList.innerHTML = cart.map((item, index) => `
        <div class="cart-item">
            <div class="d-flex justify-content-between align-items-center mb-2">
                <h6 class="mb-0">${item.name}</h6>
                <button class="btn btn-sm btn-outline-danger remove-item" data-index="${index}">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="row align-items-center">
                <div class="col-4">
                    <div class="input-group input-group-sm">
                        <button class="btn btn-outline-secondary decrease-qty" data-index="${index}">-</button>
                        <input type="number" class="form-control text-center qty-input"
                               value="${item.quantity}" min="1" max="${item.stock}" data-index="${index}">
                        <button class="btn btn-outline-secondary increase-qty" data-index="${index}">+</button>
                    </div>
                </div>
                <div class="col-4 text-center">
                    $${item.price.toFixed(2)} ea
                </div>
                <div class="col-4 text-end">
                    <strong>$${(item.price * item.quantity).toFixed(2)}</strong>
                </div>
            </div>
        </div>
    `).join('');

    // Add event listeners for cart item actions
    cartItemsList.querySelectorAll('.remove-item').forEach(btn => {
        btn.addEventListener('click', function() {
            removeFromCart(parseInt(this.dataset.index));
        });
    });

    cartItemsList.querySelectorAll('.decrease-qty').forEach(btn => {
        btn.addEventListener('click', function() {
            updateQuantity(parseInt(this.dataset.index), -1);
        });
    });

    cartItemsList.querySelectorAll('.increase-qty').forEach(btn => {
        btn.addEventListener('click', function() {
            updateQuantity(parseInt(this.dataset.index), 1);
        });
    });

    cartItemsList.querySelectorAll('.qty-input').forEach(input => {
        input.addEventListener('change', function() {
            const newQty = parseInt(this.value);
            const index = parseInt(this.dataset.index);
            if (newQty > 0 && newQty <= cart[index].stock) {
                cart[index].quantity = newQty;
                calculateTotals();
            } else {
                this.value = cart[index].quantity;
            }
        });
    });
}

function removeFromCart(index) {
    cart.splice(index, 1);
    updateCartDisplay();
    calculateTotals();
}

function updateQuantity(index, change) {
    const item = cart[index];
    const newQty = item.quantity + change;

    if (newQty > 0 && newQty <= item.stock) {
        item.quantity = newQty;
        updateCartDisplay();
        calculateTotals();
    }
}

function calculateTotals() {
    const subtotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    const discountPercentage = parseFloat(document.getElementById('discount-percentage').value) || 0;
    const discountAmount = subtotal * (discountPercentage / 100);
    const taxAmount = 0; // No tax for now
    const total = subtotal - discountAmount + taxAmount;

    document.getElementById('subtotal').textContent = subtotal.toFixed(2);
    document.getElementById('discount-amount').textContent = discountAmount.toFixed(2);
    document.getElementById('tax-amount').textContent = taxAmount.toFixed(2);
    document.getElementById('total-amount').textContent = total.toFixed(2);

    // Set amount paid to total if empty
    const amountPaidInput = document.getElementById('amount-paid');
    if (!amountPaidInput.value) {
        amountPaidInput.value = total.toFixed(2);
    }

    calculateChange();
}

function calculateChange() {
    const total = parseFloat(document.getElementById('total-amount').textContent);
    const amountPaid = parseFloat(document.getElementById('amount-paid').value) || 0;
    const change = Math.max(0, amountPaid - total);

    document.getElementById('change-amount').textContent = change.toFixed(2);
}

async function loadPrescription(prescriptionId) {
    try {
        const response = await fetch('{% url "pharmacy:api_prescription_details" %}', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ prescription_id: prescriptionId })
        });

        const data = await response.json();

        if (data.prescription) {
            // Clear current cart
            cart = [];

            // Set customer
            selectCustomer({
                id: data.prescription.patient.id,
                name: data.prescription.patient.name,
                phone: data.prescription.patient.phone
            });

            // Add prescription items to cart
            data.prescription.items.forEach(item => {
                if (item.available_stock > 0) {
                    cart.push({
                        id: item.medicine_id.toString(),
                        name: item.medicine_name,
                        price: item.unit_price,
                        quantity: Math.min(item.prescribed_quantity, item.available_stock),
                        stock: item.available_stock,
                        unit: 'unit'
                    });
                }
            });

            selectedPrescription = prescriptionId;
            updateCartDisplay();
            calculateTotals();

            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('prescriptionModal'));
            modal.hide();

            alert('Prescription loaded successfully!');
        }
    } catch (error) {
        console.error('Error loading prescription:', error);
        alert('Error loading prescription');
    }
}

async function processCheckout() {
    if (cart.length === 0) {
        alert('Cart is empty');
        return;
    }

    const total = parseFloat(document.getElementById('total-amount').textContent);
    const amountPaid = parseFloat(document.getElementById('amount-paid').value) || 0;

    if (amountPaid < total) {
        alert('Amount paid is less than total amount');
        return;
    }

    const paymentMethod = document.querySelector('input[name="payment-method"]:checked').value;

    const checkoutData = {
        customer_id: selectedCustomer?.id,
        customer_name: selectedCustomer?.name || document.getElementById('walk-in-name').value,
        customer_phone: selectedCustomer?.phone || document.getElementById('walk-in-phone').value,
        prescription_id: selectedPrescription,
        cart_items: cart.map(item => ({
            medicine_id: item.id,
            quantity: item.quantity,
            unit_price: item.price,
            discount_percentage: 0
        })),
        subtotal: parseFloat(document.getElementById('subtotal').textContent),
        discount_amount: parseFloat(document.getElementById('discount-amount').textContent),
        tax_amount: parseFloat(document.getElementById('tax-amount').textContent),
        total_amount: total,
        amount_paid: amountPaid,
        change_amount: amountPaid - total,
        payment_method: paymentMethod,
        notes: ''
    };

    try {
        const response = await fetch('{% url "pharmacy:api_checkout" %}', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(checkoutData)
        });

        const result = await response.json();

        if (result.success) {
            alert('Transaction completed successfully!\nReceipt: ' + result.receipt_number);

            // Ask if user wants to print receipt
            if (confirm('Do you want to print the receipt?')) {
                window.open(`/pharmacy/pos/receipt/${result.transaction_id}/`, '_blank');
            }

            // Reset interface
            cart = [];
            selectedCustomer = null;
            selectedPrescription = null;
            clearCustomer();
            updateCartDisplay();
            calculateTotals();
            document.getElementById('discount-percentage').value = '';
            document.getElementById('amount-paid').value = '';
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        console.error('Checkout error:', error);
        alert('An error occurred during checkout');
    }
}
