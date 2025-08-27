from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, F
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.template.loader import get_template
from django.utils import timezone
from decimal import Decimal


def home(request):
    """Home view that shows public landing or redirects to dashboard."""
    if request.user.is_authenticated:
        # Redirect authenticated users to their dashboard
        return redirect('dashboard:home')
    else:
        # Show enhanced public landing page to unauthenticated users
        context = {
            'page_type': 'landing',
            'show_navbar': True,
        }
        return render(request, 'public/enhanced_landing.html', context)


from apps.pharmacy.models import Medicine, MedicineStock, PharmacySale, PharmacySaleItem, Prescription, PrescriptionItem, DrugCategory, Manufacturer
from apps.pharmacy.forms import PharmacySaleForm, MedicineSearchForm


@login_required
def pharmacy_dashboard(request):
    """Pharmacy dashboard with key metrics and alerts."""
    context = {
        'total_medicines': Medicine.objects.filter(is_active=True).count(),
        'low_stock_medicines': Medicine.objects.filter(
            current_stock__lte=F('reorder_level')
        ).distinct().count(),
        'expired_medicines': Medicine.objects.filter(
            expiry_date__lt=timezone.now().date()
        ).count(),
        'today_sales': PharmacySale.objects.filter(
            created_at__date=timezone.now().date()
        ).aggregate(total=Sum('net_amount'))['total'] or Decimal('0.00'),
        'pending_prescriptions': Prescription.objects.filter(status='PENDING').count(),
    }
    return render(request, 'pharmacy/dashboard.html', context)


@login_required
def medicine_list_view(request):
    """List all medicines with search and filter functionality."""
    medicines = Medicine.objects.filter(is_active=True)
    
    # Search functionality
    search_form = MedicineSearchForm(request.GET)
    if search_form.is_valid():
        search_query = search_form.cleaned_data.get('search')
        category = search_form.cleaned_data.get('category')
        
        if search_query:
            medicines = medicines.filter(
                Q(generic_name__icontains=search_query) |
                Q(brand_name__icontains=search_query) |
                Q(medicine_code__icontains=search_query)
            )
        
        if category:
            medicines = medicines.filter(category=category)
    
    # Add stock information
    medicines = medicines.annotate(
        total_stock=Sum('current_stock')
    ).select_related('category', 'manufacturer')
    
    paginator = Paginator(medicines, 25)
    page_number = request.GET.get('page')
    medicines = paginator.get_page(page_number)
    
    context = {
        'medicines': medicines,
        'search_form': search_form,
    }
    return render(request, 'pharmacy/medicine_list.html', context)


@login_required
def medicine_search_api(request):
    """API endpoint for medicine search (used in sales)."""
    query = request.GET.get('q', '')
    medicines = Medicine.objects.filter(
        is_active=True
    ).filter(
        Q(generic_name__icontains=query) |
        Q(brand_name__icontains=query) |
        Q(medicine_code__icontains=query)
    ).annotate(
        total_stock=Sum('current_stock')
    )[:20]
    
    results = []
    for medicine in medicines:
        results.append({
            'id': medicine.id,
            'text': f"{medicine.generic_name} - {medicine.brand_name}",
            'generic_name': medicine.generic_name,
            'brand_name': medicine.brand_name,
            'price': str(medicine.price),
            'stock': medicine.total_stock or 0,
        })
    
    return JsonResponse({'results': results})


@login_required
def bill_list_view(request):
    """List all pharmacy sales/bills."""
    bills = PharmacySale.objects.all().select_related().order_by('-created_at')
    
    # Search functionality
    search = request.GET.get('search')
    if search:
        bills = bills.filter(
            Q(bill_number__icontains=search) |
            Q(patient_name__icontains=search) |
            Q(contact_number__icontains=search)
        )
    
    paginator = Paginator(bills, 20)
    page_number = request.GET.get('page')
    bills = paginator.get_page(page_number)
    
    return render(request, 'pharmacy/bill_list.html', {'bills': bills})


@login_required
def bill_detail_view(request, bill_id):
    """Show detailed view of a pharmacy bill."""
    bill = get_object_or_404(PharmacySale, id=bill_id)
    bill_items = PharmacySaleItem.objects.filter(sale=bill).select_related('medicine')
    
    context = {
        'bill': bill,
        'bill_items': bill_items,
    }
    return render(request, 'pharmacy/bill_detail.html', context)


@login_required
def create_sale_view(request):
    """Create a new pharmacy sale."""
    if request.method == 'POST':
        # Handle AJAX requests for adding items
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            medicine_id = request.POST.get('medicine_id')
            quantity = int(request.POST.get('quantity', 1))
            
            medicine = get_object_or_404(Medicine, id=medicine_id)
            
            # Check stock availability
            available_stock = medicine.current_stock
            
            if quantity > available_stock:
                return JsonResponse({
                    'success': False,
                    'message': f'Only {available_stock} units available in stock'
                })
            
            item_total = medicine.price * quantity
            
            return JsonResponse({
                'success': True,
                'item': {
                    'medicine_name': f"{medicine.generic_name} - {medicine.brand_name}",
                    'unit_price': str(medicine.price),
                    'quantity': quantity,
                    'total': str(item_total)
                }
            })
        
        # Handle regular form submission
        form = PharmacySaleForm(request.POST)
        if form.is_valid():
            sale = form.save()
            messages.success(request, f'Sale {sale.bill_number} created successfully!')
            return redirect('pharmacy:bill_detail', bill_id=sale.id)
    else:
        form = PharmacySaleForm()
    
    context = {
        'form': form,
        'categories': DrugCategory.objects.filter(is_active=True),
    }
    return render(request, 'pharmacy/create_sale.html', context)


@login_required
def prescription_list_view(request):
    """List all prescriptions."""
    prescriptions = Prescription.objects.all().select_related('patient', 'doctor').order_by('-created_at')
    
    # Filter options
    status = request.GET.get('status')
    if status == 'pending':
        prescriptions = prescriptions.filter(is_fulfilled=False)
    elif status == 'fulfilled':
        prescriptions = prescriptions.filter(is_fulfilled=True)
    
    paginator = Paginator(prescriptions, 20)
    page_number = request.GET.get('page')
    prescriptions = paginator.get_page(page_number)
    
    return render(request, 'pharmacy/prescription_list.html', {'prescriptions': prescriptions})


@login_required
def fulfill_prescription_view(request, prescription_id):
    """Fulfill a prescription by creating a sale."""
    prescription = get_object_or_404(Prescription, id=prescription_id)
    
    if prescription.is_fulfilled:
        messages.warning(request, 'This prescription has already been fulfilled.')
        return redirect('pharmacy:prescription_list')
    
    if request.method == 'POST':
        # Create sale from prescription
        sale = PharmacySale.objects.create(
            patient_name=f"{prescription.patient.first_name} {prescription.patient.last_name}",
            contact_number=prescription.patient.phone or '',
            total_amount=Decimal('0.00'),
            payment_status='PAID',
            served_by=request.user,
        )
        
        total_amount = Decimal('0.00')
        
        # Add prescription medicines to sale
        for prescription_med in prescription.prescriptionmedicine_set.all():
            medicine = prescription_med.medicine
            quantity = prescription_med.quantity
            unit_price = medicine.price
            item_total = unit_price * quantity
            
            PharmacySaleItem.objects.create(
                sale=sale,
                medicine=medicine,
                quantity=quantity,
                unit_price=unit_price,
                total_price=item_total
            )
            
            total_amount += item_total
        
        # Update sale total
        sale.total_amount = total_amount
        sale.save()
        
        # Mark prescription as fulfilled
        prescription.is_fulfilled = True
        prescription.fulfilled_at = timezone.now()
        prescription.save()
        
        messages.success(request, f'Prescription fulfilled successfully. Bill number: {sale.bill_number}')
        return redirect('pharmacy:bill_detail', bill_id=sale.id)
    
    prescription_medicines = PrescriptionItem.objects.filter(prescription=prescription)
    
    context = {
        'prescription': prescription,
        'prescription_medicines': prescription_medicines,
    }
    return render(request, 'pharmacy/fulfill_prescription.html', context)


@login_required
def print_bill_view(request, sale_id):
    """Print/PDF view for pharmacy bill."""
    sale = get_object_or_404(PharmacySale, id=sale_id)
    sale_items = PharmacySaleItem.objects.filter(sale=sale).select_related('medicine')
    
    context = {
        'sale': sale,
        'sale_items': sale_items,
        'print_date': timezone.now(),
    }
    
    if request.GET.get('format') == 'pdf':
        # Generate PDF (would require reportlab or weasyprint)
        template = get_template('pharmacy/bill_print_pdf.html')
        html = template.render(context)
        # Return PDF response here
        return HttpResponse('PDF generation not implemented yet', content_type='text/plain')
    
    return render(request, 'pharmacy/bill_print.html', context)


@login_required
def stock_report_view(request):
    """Stock report showing current stock levels."""
    medicines = Medicine.objects.filter(is_active=True).annotate(
        total_stock=Sum('current_stock'),
        expired_stock=Sum('stock_transactions__quantity', filter=Q(stock_transactions__transaction_type='EXPIRED'))
    ).select_related('category', 'manufacturer')
    
    # Filter options
    filter_type = request.GET.get('filter')
    if filter_type == 'low_stock':
        medicines = medicines.filter(current_stock__lte=F('reorder_level'))
    elif filter_type == 'out_of_stock':
        medicines = medicines.filter(total_stock=0)
    elif filter_type == 'expired':
        medicines = medicines.filter(expired_stock__gt=0)
    
    context = {
        'medicines': medicines,
        'filter_type': filter_type,
    }
    return render(request, 'pharmacy/stock_report.html', context)
