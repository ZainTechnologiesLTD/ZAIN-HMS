from django.contrib import admin
from django.db.models import Sum, F
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import redirect
from django.contrib import messages

from .models import (
    DrugCategory, Manufacturer, Medicine, MedicineStock, 
    PharmacySale, PharmacySaleItem, Prescription, PrescriptionItem
)


@admin.register(DrugCategory)
class DrugCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'contact_person', 'phone', 'email', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code', 'contact_person')


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('generic_name', 'brand_name', 'category', 'manufacturer', 'dosage_form', 'strength', 'selling_price', 'stock_status', 'is_active')
    list_filter = ('category', 'manufacturer', 'dosage_form', 'is_active')
    search_fields = ('generic_name', 'brand_name', 'medicine_code')
    readonly_fields = ('medicine_code',)
    
    def stock_status(self, obj):
        stock = MedicineStock.objects.filter(medicine=obj).aggregate(
            total=Sum('quantity')
        )['total'] or 0
        
        if stock <= obj.minimum_stock:
            return format_html('<span style="color: red;">Low Stock ({})</span>', stock)
        elif stock <= obj.reorder_level:
            return format_html('<span style="color: orange;">Reorder Level ({})</span>', stock)
        else:
            return format_html('<span style="color: green;">In Stock ({})</span>', stock)
    
    stock_status.short_description = 'Stock Status'


@admin.register(MedicineStock)
class MedicineStockAdmin(admin.ModelAdmin):
    list_display = ('medicine', 'transaction_type', 'quantity', 'unit_cost', 'reference_number', 'created_at')
    list_filter = ('medicine__category', 'transaction_type', 'created_at')
    search_fields = ('medicine__generic_name', 'medicine__brand_name', 'reference_number')


@admin.register(PharmacySale)
class PharmacySaleAdmin(admin.ModelAdmin):
    list_display = ('sale_number', 'customer_name', 'customer_phone', 'total_amount', 'discount_amount', 'net_amount', 'payment_method', 'created_at')
    list_filter = ('payment_method', 'created_at')
    search_fields = ('sale_number', 'customer_name', 'customer_phone')
    readonly_fields = ('sale_number', 'total_amount', 'net_amount')


@admin.register(PharmacySaleItem)
class PharmacySaleItemAdmin(admin.ModelAdmin):
    list_display = ('sale', 'medicine', 'quantity', 'unit_price', 'total_amount')
    list_filter = ('sale__created_at',)
    search_fields = ('medicine__generic_name', 'medicine__brand_name')


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('prescription_number', 'patient', 'doctor', 'created_at', 'status', 'prescription_actions')
    list_filter = ('status', 'created_at', 'doctor')
    search_fields = ('prescription_number', 'patient__first_name', 'patient__last_name', 'doctor__user__first_name')
    readonly_fields = ('prescription_number',)
    
    def prescription_actions(self, obj):
        if obj.status != 'DISPENSED':
            return format_html(
                '<a class="button" href="{}">Fulfill Prescription</a>',
                reverse('admin:pharmacy_fulfill_prescription', args=[obj.pk])
            )
        return 'Fulfilled'
    
    prescription_actions.short_description = 'Actions'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('fulfill-prescription/<int:prescription_id>/', self.admin_site.admin_view(self.fulfill_prescription), name='pharmacy_fulfill_prescription'),
        ]
        return custom_urls + urls
    
    def fulfill_prescription(self, request, prescription_id):
        # Redirect to fulfill prescription view
        return redirect('pharmacy:fulfill_prescription', prescription_id=prescription_id)


@admin.register(PrescriptionItem)
class PrescriptionItemAdmin(admin.ModelAdmin):
    list_display = ('prescription', 'medicine', 'dosage', 'frequency', 'duration', 'quantity_prescribed', 'quantity_dispensed')
    list_filter = ('prescription__created_at',)
    search_fields = ('medicine__generic_name', 'medicine__brand_name')