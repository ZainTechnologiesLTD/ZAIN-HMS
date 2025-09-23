# apps/billing/pos_views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.db.models import Q, Sum, Count, F
from django.db import models
from django.utils import timezone
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from decimal import Decimal
import json
from datetime import datetime, timedelta

from .models import (
    PoSCategory, PoSItem, PoSTransaction, PoSTransactionItem, PoSDayClose
)
from apps.patients.models import Patient
from apps.core.mixins import UnifiedSystemMixin
# from apps.core.db_router import TenantDatabaseManager  # Removed for unified ZAIN HMS


def _ensure_hospital_context(request):
    """Ensure the thread-local hospital DB context is set for billing (tenant) queries.

    If middleware already set it, this is a quick no-op. If not (e.g., direct view access
    or missing middleware), we derive from the authenticated user's hospital relation.
    """
    # ZAIN HMS unified system - no hospital context setup needed
    pass


@login_required
def pos_dashboard(request):
    """Main PoS dashboard with quick stats and navigation"""
    _ensure_hospital_context(request)
    today = timezone.now().date()
    
    # Daily stats
    today_transactions = PoSTransaction.objects.filter(
        transaction_date__date=today,
        status='COMPLETED'
    )
    
    daily_stats = {
        'total_sales': today_transactions.aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
        'transaction_count': today_transactions.count(),
        'cash_sales': today_transactions.filter(payment_method='CASH').aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
        'card_sales': today_transactions.filter(payment_method='CARD').aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
    }
    
    # Low stock items
    low_stock_items = PoSItem.objects.filter(
        is_active=True,
        current_stock__lte=F('minimum_stock')
    )[:5]
    
    # Recent transactions
    recent_transactions = PoSTransaction.objects.select_related('patient', 'cashier').order_by('-created_at')[:10]
    
    context = {
        'daily_stats': daily_stats,
        'low_stock_items': low_stock_items,
        'recent_transactions': recent_transactions,
        'page_title': 'Point of Sale Dashboard'
    }
    
    return render(request, 'billing/pos/dashboard.html', context)


@login_required
def pos_sale_interface(request):
    """Main PoS sale interface - the cash register"""
    _ensure_hospital_context(request)
    categories = PoSCategory.objects.filter(is_active=True).prefetch_related('items')
    
    # Get items by category for quick access
    items_by_category = {}
    for category in categories:
        items_by_category[category.id] = category.items.filter(is_active=True, current_stock__gt=0)
    
    context = {
        'categories': categories,
        'items_by_category': items_by_category,
        'page_title': 'Point of Sale'
    }
    
    return render(request, 'billing/pos/sale_interface.html', context)


@login_required
def pos_search_items(request):
    """AJAX endpoint to search items"""
    _ensure_hospital_context(request)
    query = request.GET.get('q', '').strip()
    
    if not query:
        return JsonResponse({'items': []})
    
    items = PoSItem.objects.filter(
        Q(name__icontains=query) |
        Q(item_code__icontains=query) |
        Q(barcode__icontains=query),
        is_active=True,
        current_stock__gt=0
    )[:20]
    
    items_data = []
    for item in items:
        items_data.append({
            'id': item.id,
            'code': item.item_code,
            'name': item.name,
            'price': float(item.selling_price),
            'stock': item.current_stock,
            'taxable': item.is_taxable,
            'tax_rate': float(item.tax_rate),
            'prescription_required': item.is_prescription_required
        })
    
    return JsonResponse({'items': items_data})


@login_required
def pos_search_patients(request):
    """AJAX endpoint to search patients"""
    _ensure_hospital_context(request)
    query = request.GET.get('q', '').strip()
    
    if not query:
        return JsonResponse({'patients': []})
    
    patients = Patient.objects.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(phone__icontains=query) |
        Q(patient_id__icontains=query)
    )[:10]
    
    patients_data = []
    for patient in patients:
        patients_data.append({
            'id': patient.id,
            'patient_id': patient.patient_id,
            'name': patient.get_full_name(),
            'phone': patient.phone,
            'email': patient.email
        })
    
    return JsonResponse({'patients': patients_data})


@login_required
def pos_create_transaction(request):
    """Create a new PoS transaction"""
    _ensure_hospital_context(request)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Create transaction
            transaction = PoSTransaction.objects.create(
                patient_id=data.get('patient_id') if data.get('patient_id') else None,
                customer_name=data.get('customer_name', ''),
                customer_phone=data.get('customer_phone', ''),
                payment_method=data.get('payment_method', 'CASH'),
                amount_received=Decimal(data.get('amount_received', '0')),
                discount_amount=Decimal(data.get('discount_amount', '0')),
                notes=data.get('notes', ''),
                cashier=request.user,
                status='COMPLETED'
            )
            
            # Add transaction items
            for item_data in data.get('items', []):
                item = PoSItem.objects.get(id=item_data['item_id'])
                
                # Check stock availability
                if item.current_stock < item_data['quantity']:
                    transaction.delete()  # Rollback
                    return JsonResponse({
                        'success': False,
                        'error': f'Insufficient stock for {item.name}. Available: {item.current_stock}'
                    })
                
                # Create transaction item
                PoSTransactionItem.objects.create(
                    transaction=transaction,
                    item=item,
                    quantity=item_data['quantity'],
                    unit_price=Decimal(item_data.get('unit_price', item.selling_price)),
                    discount_percentage=Decimal(item_data.get('discount_percentage', '0')),
                    prescription_number=item_data.get('prescription_number', ''),
                    prescribed_by_id=item_data.get('prescribed_by_id') if item_data.get('prescribed_by_id') else None
                )
                
                # Update stock
                item.current_stock -= item_data['quantity']
                item.save()
            
            # Recalculate transaction totals
            transaction.calculate_totals()
            transaction.save()
            
            return JsonResponse({
                'success': True,
                'transaction_id': str(transaction.id),
                'transaction_number': transaction.transaction_number,
                'total_amount': float(transaction.total_amount)
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


class PoSTransactionListView(LoginRequiredMixin, ListView):
    """List all PoS transactions"""
    model = PoSTransaction
    template_name = 'billing/pos/transaction_list.html'
    context_object_name = 'transactions'
    paginate_by = 25
    
    def get_queryset(self):
        _ensure_hospital_context(self.request)
        queryset = PoSTransaction.objects.select_related('patient', 'cashier').order_by('-created_at')

        # Filter by date range
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')

        if date_from:
            queryset = queryset.filter(transaction_date__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(transaction_date__date__lte=date_to)

        # Filter by payment method
        payment_method = self.request.GET.get('payment_method')
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)

        # Filter by cashier
        cashier = self.request.GET.get('cashier')
        if cashier:
            queryset = queryset.filter(cashier_id=cashier)

        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'PoS Transactions'
        context['payment_methods'] = PoSTransaction.PAYMENT_METHODS
        
        # Get cashiers for filter
        from apps.accounts.models import CustomUser as User
        context['cashiers'] = User.objects.filter(
            pos_transactions__isnull=False
        ).distinct().order_by('first_name', 'last_name')
        
        return context


class PoSTransactionDetailView(LoginRequiredMixin, DetailView):
    """View PoS transaction details"""
    model = PoSTransaction
    template_name = 'billing/pos/transaction_detail.html'
    context_object_name = 'transaction'
    
    def get_context_data(self, **kwargs):
        _ensure_hospital_context(self.request)
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'PoS Transaction {self.object.transaction_number}'
        return context


@login_required
def pos_transaction_receipt(request, pk):
    """Generate transaction receipt"""
    transaction = get_object_or_404(PoSTransaction, pk=pk)
    
    context = {
        'transaction': transaction,
        'hospital': request.user.hospital if hasattr(request.user, 'hospital') else None,
    }
    
    return render(request, 'billing/pos/receipt.html', context)


class PoSItemListView(LoginRequiredMixin, ListView):
    """List and manage PoS items"""
    model = PoSItem
    template_name = 'billing/pos/item_list.html'
    context_object_name = 'items'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = PoSItem.objects.select_related('category').order_by('name')
        
        # Search filter
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(item_code__icontains=search) |
                Q(description__icontains=search)
            )
        
        # Category filter
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        
        # Stock filter
        stock_filter = self.request.GET.get('stock')
        if stock_filter == 'low':
            queryset = queryset.filter(current_stock__lte=F('minimum_stock'))
        elif stock_filter == 'out':
            queryset = queryset.filter(current_stock=0)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'PoS Items'
        context['categories'] = PoSCategory.objects.filter(is_active=True).order_by('name')
        return context


class PoSItemCreateView(UnifiedSystemMixin, LoginRequiredMixin, CreateView):
    """Create new PoS item"""
    model = PoSItem
    template_name = 'billing/pos/item_form.html'
    fields = [
        'category', 'item_code', 'name', 'description', 'item_type',
        'cost_price', 'selling_price', 'discount_price',
        'current_stock', 'minimum_stock', 'maximum_stock',
        'is_taxable', 'tax_rate', 'is_prescription_required',
        'barcode', 'manufacturer', 'batch_number', 'expiry_date'
    ]
    success_url = reverse_lazy('billing:pos_item_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'PoS item "{form.instance.name}" created successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Add New PoS Item'
        return context


@login_required
def pos_daily_report(request):
    """Generate daily sales report"""
    date_str = request.GET.get('date')
    if date_str:
        report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        report_date = timezone.now().date()
    
    # Get transactions for the day
    transactions = PoSTransaction.objects.filter(
        transaction_date__date=report_date,
        status='COMPLETED'
    ).select_related('patient', 'cashier')
    
    # Calculate totals
    summary = transactions.aggregate(
        total_sales=Sum('total_amount'),
        total_tax=Sum('tax_amount'),
        total_discount=Sum('discount_amount'),
        transaction_count=Count('id')
    )
    
    # Payment method breakdown
    payment_breakdown = {}
    for method_code, method_name in PoSTransaction.PAYMENT_METHODS:
        amount = transactions.filter(payment_method=method_code).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        payment_breakdown[method_name] = amount
    
    # Top selling items
    top_items = PoSTransactionItem.objects.filter(
        transaction__transaction_date__date=report_date,
        transaction__status='COMPLETED'
    ).values(
        'item__name', 'item__item_code'
    ).annotate(
        total_qty=Sum('quantity'),
        total_amount=Sum('total_amount')
    ).order_by('-total_amount')[:10]
    
    context = {
        'report_date': report_date,
        'transactions': transactions,
        'summary': summary,
        'payment_breakdown': payment_breakdown,
        'top_items': top_items,
        'page_title': f'Daily PoS Report - {report_date}'
    }
    
    return render(request, 'billing/pos/daily_report.html', context)


@login_required
def pos_close_day(request):
    """Close the day and generate closing report"""
    today = timezone.now().date()
    
    # Check if day is already closed
    existing_close = PoSDayClose.objects.filter(
        date=today,
        cashier=request.user,
        is_closed=True
    ).first()
    
    if existing_close:
        messages.warning(request, f'Day {today} has already been closed.')
        return redirect('billing:pos_dashboard')
    
    if request.method == 'POST':
        opening_cash = Decimal(request.POST.get('opening_cash', '0'))
        closing_cash = Decimal(request.POST.get('closing_cash', '0'))
        notes = request.POST.get('notes', '')
        
        # Calculate day's transactions
        day_transactions = PoSTransaction.objects.filter(
            transaction_date__date=today,
            cashier=request.user,
            status='COMPLETED'
        )
        
        totals = day_transactions.aggregate(
            total_transactions=Count('id'),
            total_sales=Sum('total_amount'),
            total_tax=Sum('tax_amount'),
            total_discount=Sum('discount_amount'),
            cash_payments=Sum('total_amount', filter=Q(payment_method='CASH')),
            card_payments=Sum('total_amount', filter=Q(payment_method='CARD')),
            digital_payments=Sum('total_amount', filter=Q(payment_method='DIGITAL')),
            credit_sales=Sum('total_amount', filter=Q(payment_method='CREDIT'))
        )
        
        # Create day close record
        day_close = PoSDayClose.objects.create(
            date=today,
            cashier=request.user,
            opening_cash=opening_cash,
            closing_cash=closing_cash,
            cash_sales=totals['cash_payments'] or 0,
            cash_variance=closing_cash - opening_cash - (totals['cash_payments'] or 0),
            total_transactions=totals['total_transactions'] or 0,
            total_sales=totals['total_sales'] or 0,
            total_tax=totals['total_tax'] or 0,
            total_discount=totals['total_discount'] or 0,
            cash_payments=totals['cash_payments'] or 0,
            card_payments=totals['card_payments'] or 0,
            digital_payments=totals['digital_payments'] or 0,
            credit_sales=totals['credit_sales'] or 0,
            notes=notes,
            is_closed=True
        )
        
        messages.success(request, f'Day {today} closed successfully!')
        return redirect('billing:pos_day_close_detail', pk=day_close.pk)
    
    # GET request - show closing form
    day_transactions = PoSTransaction.objects.filter(
        transaction_date__date=today,
        cashier=request.user,
        status='COMPLETED'
    )
    
    daily_summary = day_transactions.aggregate(
        total_sales=Sum('total_amount'),
        cash_sales=Sum('total_amount', filter=Q(payment_method='CASH')),
        transaction_count=Count('id')
    )
    
    context = {
        'today': today,
        'daily_summary': daily_summary,
        'page_title': 'Close Day'
    }
    
    return render(request, 'billing/pos/close_day.html', context)


class PoSDayCloseDetailView(LoginRequiredMixin, DetailView):
    """View day close details"""
    model = PoSDayClose
    template_name = 'billing/pos/day_close_detail.html'
    context_object_name = 'day_close'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Day Close - {self.object.date}'
        return context
