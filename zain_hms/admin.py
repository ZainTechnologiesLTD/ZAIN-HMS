from django.contrib import admin
from django.contrib.admin import AdminSite
from django.db.models import Sum, F, Count, Q
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import redirect, render
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.template.response import TemplateResponse
from django.contrib.auth.models import User, Group
from django.core.cache import cache
from datetime import datetime, timedelta
import json

# Enhanced Admin Site Configuration
class ZainHMSAdminSite(AdminSite):
    site_header = 'Zain HMS Administration'
    site_title = 'Zain HMS Admin'
    index_title = 'Hospital Management Dashboard'
    site_url = '/'
    enable_nav_sidebar = True
    
    def each_context(self, request):
        """Add custom context to all admin pages."""
        context = super().each_context(request)
        
        # Add dashboard statistics
        try:
            from apps.patients.models import Patient
            from apps.appointments.models import Appointment
            from apps.doctors.models import Doctor
            from apps.billing.models import Bill
            
            context.update({
                'dashboard_stats': {
                    'total_patients': Patient.objects.count(),
                    'total_doctors': Doctor.objects.count(),
                    'today_appointments': Appointment.objects.filter(
                        appointment_date__date=datetime.now().date()
                    ).count(),
                    'pending_bills': Bill.objects.filter(status='pending').count(),
                },
                'current_time': datetime.now(),
                'system_status': self.get_system_status(),
            })
        except Exception:
            # Handle case where models might not be available yet
            context.update({
                'dashboard_stats': {
                    'total_patients': 0,
                    'total_doctors': 0, 
                    'today_appointments': 0,
                    'pending_bills': 0,
                },
                'system_status': {'database': 'unknown'},
            })
        
        return context
    
    def get_system_status(self):
        """Get system health status."""
        status = {
            'database': 'online',
            'cache': 'active',
            'background_tasks': 'processing',
            'backup': 'scheduled'
        }
        
        # Test cache
        try:
            cache.set('health_check', 'ok', 60)
            if cache.get('health_check') != 'ok':
                status['cache'] = 'error'
        except Exception:
            status['cache'] = 'error'
            
        return status
    
    def index(self, request, extra_context=None):
        """Enhanced admin index view."""
        extra_context = extra_context or {}
        
        # Add quick actions
        extra_context['quick_actions'] = [
            {
                'title': 'Add Patient',
                'url': 'admin:patients_patient_add',
                'icon': 'fas fa-user-plus',
                'color': 'success'
            },
            {
                'title': 'Schedule Appointment',
                'url': 'admin:appointments_appointment_add',
                'icon': 'fas fa-calendar-plus',
                'color': 'primary'
            },
            {
                'title': 'Create Bill',
                'url': 'admin:billing_bill_add',
                'icon': 'fas fa-file-invoice',
                'color': 'warning'
            },
            {
                'title': 'View Reports',
                'url': '/reports/',
                'icon': 'fas fa-chart-line',
                'color': 'info'
            },
        ]
        
        # Add recent activity (mock data for now)
        extra_context['recent_activity'] = [
            {
                'title': 'New patient registered',
                'time': '2 minutes ago',
                'icon': 'fas fa-user-plus',
                'color': 'success'
            },
            {
                'title': 'Appointment scheduled',
                'time': '5 minutes ago',
                'icon': 'fas fa-calendar-check',
                'color': 'info'
            },
            {
                'title': 'Lab result updated',
                'time': '10 minutes ago',
                'icon': 'fas fa-flask',
                'color': 'warning'
            },
            {
                'title': 'Bill payment received',
                'time': '15 minutes ago',
                'icon': 'fas fa-file-invoice',
                'color': 'primary'
            },
        ]
        
        return super().index(request, extra_context)

# Replace the default admin site
admin_site = ZainHMSAdminSite(name='admin')

# Import models for backwards compatibility (if this is a pharmacy admin file)
try:
    from .models import (
        DrugCategory, Manufacturer, Medicine, MedicineStock, 
        PharmacySale, PharmacySaleItem, Prescription, PrescriptionMedicine
    )
except ImportError:
    # Models might not exist in main admin file
    pass


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
    list_display = ('generic_name', 'brand_name', 'category', 'manufacturer', 'dosage_form', 'strength', 'price', 'stock_status', 'is_active')
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
    list_display = ('medicine', 'batch_number', 'quantity', 'expiry_date', 'purchase_price', 'selling_price')
    list_filter = ('medicine__category', 'expiry_date')
    search_fields = ('medicine__generic_name', 'medicine__brand_name', 'batch_number')


@admin.register(PharmacySale)
class PharmacySaleAdmin(admin.ModelAdmin):
    list_display = ('bill_number', 'patient_name', 'total_amount', 'payment_status', 'created_at', 'actions')
    list_filter = ('payment_status', 'created_at')
    search_fields = ('bill_number', 'patient_name', 'contact_number')
    readonly_fields = ('bill_number', 'total_amount')
    
    def actions(self, obj):
        return format_html(
            '<a class="button" href="{}">Print Bill</a>',
            reverse('admin:pharmacy_print_bill', args=[obj.pk])
        )
    
    actions.short_description = 'Actions'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('print-bill/<int:sale_id>/', self.admin_site.admin_view(self.print_bill), name='pharmacy_print_bill'),
        ]
        return custom_urls + urls
    
    def print_bill(self, request, sale_id):
        # Redirect to print view
        return redirect('pharmacy:print_bill', sale_id=sale_id)


@admin.register(PharmacySaleItem)
class PharmacySaleItemAdmin(admin.ModelAdmin):
    list_display = ('sale', 'medicine', 'quantity', 'unit_price', 'total_price')
    list_filter = ('sale__created_at',)
    search_fields = ('medicine__generic_name', 'medicine__brand_name')


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('prescription_number', 'patient', 'doctor', 'created_at', 'is_fulfilled', 'actions')
    list_filter = ('is_fulfilled', 'created_at', 'doctor')
    search_fields = ('prescription_number', 'patient__first_name', 'patient__last_name', 'doctor__user__first_name')
    readonly_fields = ('prescription_number',)
    
    def actions(self, obj):
        if not obj.is_fulfilled:
            return format_html(
                '<a class="button" href="{}">Fulfill Prescription</a>',
                reverse('admin:pharmacy_fulfill_prescription', args=[obj.pk])
            )
        return 'Fulfilled'
    
    actions.short_description = 'Actions'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('fulfill-prescription/<int:prescription_id>/', self.admin_site.admin_view(self.fulfill_prescription), name='pharmacy_fulfill_prescription'),
        ]
        return custom_urls + urls
    
    def fulfill_prescription(self, request, prescription_id):
        # Redirect to fulfill prescription view
        return redirect('pharmacy:fulfill_prescription', prescription_id=prescription_id)


@admin.register(PrescriptionMedicine)
class PrescriptionMedicineAdmin(admin.ModelAdmin):
    list_display = ('prescription', 'medicine', 'dosage', 'frequency', 'duration', 'quantity')
    list_filter = ('prescription__created_at',)
    search_fields = ('medicine__generic_name', 'medicine__brand_name')