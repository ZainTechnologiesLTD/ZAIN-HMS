# apps/pharmacy/pos_views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from decimal import Decimal
import json
from datetime import datetime, timedelta

from .models import (
    Medicine, PharmacyPoSTransaction, PharmacyPoSTransactionItem, 
    PharmacyPoSPayment, PharmacyPoSDayClose, PharmacyBill, 
    Prescription, Patient
)
from apps.patients.models import Patient


@login_required
def pos_dashboard(request):
    """Pharmacy PoS Dashboard"""
    today = timezone.now().date()
    
    # Today's statistics
    today_transactions = PharmacyPoSTransaction.objects.filter(
        date__date=today,
        status='COMPLETED'
    )
    
    today_stats = {
        'total_sales': today_transactions.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0.00'),
        'total_transactions': today_transactions.count(),
        'cash_sales': today_transactions.filter(
            payment_method='CASH'
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
        'card_sales': today_transactions.filter(
            payment_method='CARD'
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
    }
    
    # Recent transactions
    recent_transactions = PharmacyPoSTransaction.objects.filter(
        cashier=request.user
    ).order_by('-created_at')[:10]
    
    # Low stock medicines
    low_stock_medicines = Medicine.objects.filter(
        current_stock__lte=10,
        is_active=True
    ).order_by('current_stock')[:5]
    
    # Check if day is open
    day_close = PharmacyPoSDayClose.objects.filter(
        date=today,
        cashier=request.user,
        is_closed=False
    ).first()
    
    context = {
        'today_stats': today_stats,
        'recent_transactions': recent_transactions,
        'low_stock_medicines': low_stock_medicines,
        'day_is_open': day_close is not None,
        'current_date': today,
    }
    
    return render(request, 'pharmacy/pos/dashboard.html', context)


@login_required
def pos_sale_interface(request):
    """Main PoS sale interface"""
    # Get medicines with stock
    medicines = Medicine.objects.filter(
        is_active=True,
        current_stock__gt=0
    ).order_by('name')
    
    # Get recent customers for quick access
    recent_customers = Patient.objects.order_by('-created_at')[:10]
    
    # Get pending prescriptions that need fulfillment
    pending_prescriptions = Prescription.objects.filter(
        status='PENDING'
    ).order_by('-created_at')[:10]
    
    context = {
        'medicines': medicines,
        'recent_customers': recent_customers,
        'pending_prescriptions': pending_prescriptions,
    }
    
    return render(request, 'pharmacy/pos/sale_interface.html', context)


@csrf_exempt
@login_required
def api_search_medicines(request):
    """AJAX API for medicine search"""
    if request.method == 'POST':
        data = json.loads(request.body)
        query = data.get('query', '').strip()
        
        if len(query) < 2:
            return JsonResponse({'medicines': []})
        
        medicines = Medicine.objects.filter(
            Q(name__icontains=query) |
            Q(generic_name__icontains=query) |
            Q(batch_number__icontains=query),
            is_active=True,
            current_stock__gt=0
        )[:20]
        
        medicine_data = []
        for medicine in medicines:
            medicine_data.append({
                'id': medicine.id,
                'name': medicine.name,
                'generic_name': medicine.generic_name,
                'strength': medicine.strength,
                'unit': medicine.unit,
                'price': float(medicine.unit_price),
                'stock': medicine.current_stock,
                'batch_number': medicine.batch_number,
                'expiry_date': medicine.expiry_date.strftime('%Y-%m-%d') if medicine.expiry_date else None,
            })
        
        return JsonResponse({'medicines': medicine_data})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
@login_required
def api_search_patients(request):
    """AJAX API for patient search"""
    if request.method == 'POST':
        data = json.loads(request.body)
        query = data.get('query', '').strip()
        
        if len(query) < 2:
            return JsonResponse({'patients': []})
        
        patients = Patient.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(phone__icontains=query) |
            Q(email__icontains=query)
        )[:20]
        
        patient_data = []
        for patient in patients:
            patient_data.append({
                'id': patient.id,
                'name': patient.get_full_name(),
                'phone': patient.phone,
                'email': patient.email,
                'date_of_birth': patient.date_of_birth.strftime('%Y-%m-%d') if patient.date_of_birth else None,
            })
        
        return JsonResponse({'patients': patient_data})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
@login_required
def api_get_prescription_details(request):
    """Get prescription details for PoS"""
    if request.method == 'POST':
        data = json.loads(request.body)
        prescription_id = data.get('prescription_id')
        
        try:
            prescription = Prescription.objects.get(id=prescription_id)
            items_data = []
            
            for item in prescription.items.all():
                if item.medicine.current_stock > 0:
                    items_data.append({
                        'medicine_id': item.medicine.id,
                        'medicine_name': item.medicine.name,
                        'prescribed_quantity': item.quantity,
                        'available_stock': item.medicine.current_stock,
                        'unit_price': float(item.medicine.unit_price),
                        'instructions': item.instructions,
                    })
            
            return JsonResponse({
                'prescription': {
                    'id': prescription.id,
                    'patient': {
                        'id': prescription.patient.id,
                        'name': prescription.patient.get_full_name(),
                        'phone': prescription.patient.phone,
                    },
                    'doctor': prescription.doctor.get_full_name() if prescription.doctor else 'N/A',
                    'date': prescription.date.strftime('%Y-%m-%d'),
                    'items': items_data,
                }
            })
            
        except Prescription.DoesNotExist:
            return JsonResponse({'error': 'Prescription not found'}, status=404)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
@login_required
def api_process_checkout(request):
    """Process PoS checkout"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            with transaction.atomic():
                # Create transaction
                pos_transaction = PharmacyPoSTransaction.objects.create(
                    cashier=request.user,
                    customer_id=data.get('customer_id') if data.get('customer_id') else None,
                    customer_name=data.get('customer_name', ''),
                    customer_phone=data.get('customer_phone', ''),
                    prescription_id=data.get('prescription_id') if data.get('prescription_id') else None,
                    payment_method=data.get('payment_method', 'CASH'),
                    subtotal=Decimal(str(data.get('subtotal', '0.00'))),
                    discount_amount=Decimal(str(data.get('discount_amount', '0.00'))),
                    tax_amount=Decimal(str(data.get('tax_amount', '0.00'))),
                    total_amount=Decimal(str(data.get('total_amount', '0.00'))),
                    amount_paid=Decimal(str(data.get('amount_paid', '0.00'))),
                    change_amount=Decimal(str(data.get('change_amount', '0.00'))),
                    notes=data.get('notes', ''),
                    status='COMPLETED'
                )
                
                # Process cart items
                for item_data in data.get('cart_items', []):
                    medicine = Medicine.objects.get(id=item_data['medicine_id'])
                    quantity = int(item_data['quantity'])
                    
                    # Check stock availability
                    if medicine.current_stock < quantity:
                        raise ValueError(f"Insufficient stock for {medicine.name}")
                    
                    # Create transaction item
                    PharmacyPoSTransactionItem.objects.create(
                        transaction=pos_transaction,
                        medicine=medicine,
                        quantity=quantity,
                        unit_price=Decimal(str(item_data['unit_price'])),
                        discount_percentage=Decimal(str(item_data.get('discount_percentage', '0.00'))),
                    )
                    
                    # Update stock
                    medicine.current_stock -= quantity
                    medicine.save()
                    
                    # Create stock transaction record
                    from .models import MedicineStock
                    MedicineStock.objects.create(
                        medicine=medicine,
                        transaction_type='SALE',
                        quantity=-quantity,
                        unit_cost=medicine.unit_price,
                        reference_number=pos_transaction.receipt_number,
                        notes=f"PoS Sale - {pos_transaction.receipt_number}",
                        created_by=request.user
                    )
                
                # Handle split payments if needed
                if data.get('split_payments'):
                    for payment_data in data['split_payments']:
                        PharmacyPoSPayment.objects.create(
                            transaction=pos_transaction,
                            payment_method=payment_data['method'],
                            amount=Decimal(str(payment_data['amount'])),
                            reference_number=payment_data.get('reference', ''),
                            notes=payment_data.get('notes', '')
                        )
                
                # Create pharmacy bill if customer is a patient
                if pos_transaction.customer:
                    pharmacy_bill = PharmacyBill.objects.create(
                        patient=pos_transaction.customer,
                        prescription=pos_transaction.prescription,
                        pos_transaction=pos_transaction,
                        subtotal=pos_transaction.subtotal,
                        discount_amount=pos_transaction.discount_amount,
                        tax_amount=pos_transaction.tax_amount,
                        total_amount=pos_transaction.total_amount,
                        paid_amount=pos_transaction.amount_paid,
                        status='PAID' if pos_transaction.amount_paid >= pos_transaction.total_amount else 'PARTIAL',
                        created_by=request.user
                    )
                
                # Update prescription status if applicable
                if pos_transaction.prescription:
                    pos_transaction.prescription.status = 'DISPENSED'
                    pos_transaction.prescription.save()
                
                return JsonResponse({
                    'success': True,
                    'transaction_id': str(pos_transaction.id),
                    'receipt_number': pos_transaction.receipt_number,
                    'message': 'Transaction completed successfully'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def transaction_history(request):
    """View transaction history"""
    transactions = PharmacyPoSTransaction.objects.filter(
        cashier=request.user
    ).order_by('-created_at')
    
    # Date filtering
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if date_from:
        transactions = transactions.filter(date__date__gte=date_from)
    if date_to:
        transactions = transactions.filter(date__date__lte=date_to)
    
    # Status filtering
    status = request.GET.get('status')
    if status:
        transactions = transactions.filter(status=status)
    
    # Payment method filtering
    payment_method = request.GET.get('payment_method')
    if payment_method:
        transactions = transactions.filter(payment_method=payment_method)
    
    paginator = Paginator(transactions, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'transactions': page_obj,
        'total_amount': transactions.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0.00'),
    }
    
    return render(request, 'pharmacy/pos/transaction_history.html', context)


@login_required
def transaction_detail(request, transaction_id):
    """View transaction details"""
    transaction = get_object_or_404(PharmacyPoSTransaction, id=transaction_id)
    
    context = {
        'transaction': transaction,
        'items': transaction.items.all(),
        'payments': transaction.payments.all() if hasattr(transaction, 'payments') else [],
    }
    
    return render(request, 'pharmacy/pos/transaction_detail.html', context)


@login_required
def print_receipt(request, transaction_id):
    """Print receipt for transaction"""
    transaction = get_object_or_404(PharmacyPoSTransaction, id=transaction_id)
    
    context = {
        'transaction': transaction,
        'items': transaction.items.all(),
    }
    
    return render(request, 'pharmacy/pos/receipt_print.html', context)


@login_required
def day_close(request):
    """Daily closing procedures"""
    today = timezone.now().date()
    
    # Check if day is already closed
    existing_close = PharmacyPoSDayClose.objects.filter(
        date=today,
        cashier=request.user,
        is_closed=True
    ).first()
    
    if existing_close:
        messages.warning(request, 'Day has already been closed.')
        return redirect('pharmacy:pos_dashboard')
    
    if request.method == 'POST':
        with transaction.atomic():
            # Calculate daily totals
            today_transactions = PharmacyPoSTransaction.objects.filter(
                date__date=today,
                cashier=request.user
            )
            
            completed_transactions = today_transactions.filter(status='COMPLETED')
            
            day_close_data = {
                'date': today,
                'cashier': request.user,
                'total_transactions': today_transactions.count(),
                'completed_transactions': completed_transactions.count(),
                'cancelled_transactions': today_transactions.filter(status='CANCELLED').count(),
                'refunded_transactions': today_transactions.filter(status='REFUNDED').count(),
                'gross_sales': completed_transactions.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
                'total_discounts': completed_transactions.aggregate(total=Sum('discount_amount'))['total'] or Decimal('0.00'),
                'total_tax': completed_transactions.aggregate(total=Sum('tax_amount'))['total'] or Decimal('0.00'),
                'cash_sales': completed_transactions.filter(payment_method='CASH').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
                'card_sales': completed_transactions.filter(payment_method='CARD').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
                'mobile_money_sales': completed_transactions.filter(payment_method='MOBILE_MONEY').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
                'insurance_sales': completed_transactions.filter(payment_method='INSURANCE').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
                'credit_sales': completed_transactions.filter(payment_method='CREDIT').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
                'opening_cash': Decimal(request.POST.get('opening_cash', '0.00')),
                'closing_cash_actual': Decimal(request.POST.get('closing_cash', '0.00')),
                'notes': request.POST.get('notes', ''),
                'is_closed': True,
                'closed_at': timezone.now(),
            }
            
            # Calculate net sales and expected closing cash
            day_close_data['net_sales'] = day_close_data['gross_sales'] - day_close_data['total_discounts']
            day_close_data['closing_cash_expected'] = day_close_data['opening_cash'] + day_close_data['cash_sales']
            day_close_data['cash_variance'] = day_close_data['closing_cash_actual'] - day_close_data['closing_cash_expected']
            
            PharmacyPoSDayClose.objects.create(**day_close_data)
            
            messages.success(request, 'Day closed successfully!')
            return redirect('pharmacy:pos_dashboard')
    
    # Calculate summary for display
    today_transactions = PharmacyPoSTransaction.objects.filter(
        date__date=today,
        cashier=request.user,
        status='COMPLETED'
    )
    
    summary = {
        'total_transactions': today_transactions.count(),
        'gross_sales': today_transactions.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
        'cash_sales': today_transactions.filter(payment_method='CASH').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
        'card_sales': today_transactions.filter(payment_method='CARD').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
        'total_discounts': today_transactions.aggregate(total=Sum('discount_amount'))['total'] or Decimal('0.00'),
    }
    
    context = {
        'summary': summary,
        'today': today,
    }
    
    return render(request, 'pharmacy/pos/day_close.html', context)
