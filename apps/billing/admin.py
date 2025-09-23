from django.contrib import admin
from .models import (
    Bill, PoSCategory, PoSItem, PoSTransaction, 
    PoSTransactionItem, PoSDayClose
)

@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Bill._meta.fields]  # Display all fields in the admin interface


# ===== POINT OF SALE ADMIN =====

@admin.register(PoSCategory)
class PoSCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']


@admin.register(PoSItem)
class PoSItemAdmin(admin.ModelAdmin):
    list_display = [
        'item_code', 'name', 'category', 'selling_price', 
        'current_stock', 'is_active', 'is_low_stock'
    ]
    list_filter = [
        'category', 'item_type', 'is_active', 'is_taxable', 
        'is_prescription_required', 'created_at'
    ]
    search_fields = ['name', 'item_code', 'barcode', 'manufacturer']
    ordering = ['name']
    readonly_fields = ['profit_margin', 'is_low_stock', 'is_expired']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'item_code', 'name', 'description', 'item_type')
        }),
        ('Pricing', {
            'fields': ('cost_price', 'selling_price', 'discount_price', 'profit_margin')
        }),
        ('Inventory', {
            'fields': ('current_stock', 'minimum_stock', 'maximum_stock', 'is_low_stock')
        }),
        ('Tax Settings', {
            'fields': ('is_taxable', 'tax_rate')
        }),
        ('Additional Details', {
            'fields': (
                'is_prescription_required', 'barcode', 'manufacturer', 
                'batch_number', 'expiry_date', 'is_expired'
            ),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        })
    )
    
    def is_low_stock(self, obj):
        return obj.is_low_stock
    is_low_stock.boolean = True
    is_low_stock.short_description = 'Low Stock'


class PoSTransactionItemInline(admin.TabularInline):
    model = PoSTransactionItem
    extra = 0
    readonly_fields = ['subtotal', 'tax_amount', 'total_amount']


@admin.register(PoSTransaction)
class PoSTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'transaction_number', 'get_customer_name', 'total_amount', 
        'payment_method', 'status', 'cashier', 'transaction_date'
    ]
    list_filter = ['status', 'payment_method', 'transaction_date', 'cashier']
    search_fields = [
        'transaction_number', 'customer_name', 'customer_phone',
        'patient__first_name', 'patient__last_name'
    ]
    readonly_fields = [
        'transaction_number', 'subtotal', 'tax_amount', 
        'total_amount', 'change_amount'
    ]
    inlines = [PoSTransactionItemInline]
    
    fieldsets = (
        ('Transaction Info', {
            'fields': ('transaction_number', 'transaction_date', 'status')
        }),
        ('Customer Info', {
            'fields': ('patient', 'customer_name', 'customer_phone')
        }),
        ('Payment Details', {
            'fields': (
                'payment_method', 'subtotal', 'tax_amount', 
                'discount_amount', 'total_amount', 'amount_received', 'change_amount'
            )
        }),
        ('Additional Info', {
            'fields': ('notes', 'cashier'),
            'classes': ('collapse',)
        })
    )
    
    def get_customer_name(self, obj):
        if obj.patient:
            return obj.patient.get_full_name()
        return obj.customer_name or 'Walk-in Customer'
    get_customer_name.short_description = 'Customer'


@admin.register(PoSDayClose)
class PoSDayCloseAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'cashier', 'total_sales', 'total_transactions',
        'cash_variance', 'is_closed'
    ]
    list_filter = ['date', 'cashier', 'is_closed']
    readonly_fields = [
        'total_transactions', 'total_sales', 'total_tax', 'total_discount',
        'cash_payments', 'card_payments', 'digital_payments', 'credit_sales',
        'cash_variance'
    ]
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('date', 'cashier', 'is_closed')
        }),
        ('Cash Management', {
            'fields': ('opening_cash', 'closing_cash', 'cash_sales', 'cash_variance')
        }),
        ('Sales Summary', {
            'fields': ('total_transactions', 'total_sales', 'total_tax', 'total_discount')
        }),
        ('Payment Breakdown', {
            'fields': ('cash_payments', 'card_payments', 'digital_payments', 'credit_sales')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        })
    )
