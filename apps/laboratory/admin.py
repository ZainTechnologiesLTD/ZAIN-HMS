from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Avg
from .models import (
    LabSection, TestCategory, LabTest, LabOrder, LabOrderItem, 
    LabResult, LabEquipment, DigitalSignature, LabReportTemplate
)


@admin.register(LabSection)
class LabSectionAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'head_of_section', 'requires_digital_signature', 'is_active', 'test_count')
    list_filter = ('is_active', 'requires_digital_signature')
    search_fields = ('name', 'code', 'description')
    filter_horizontal = ()
    
    def test_count(self, obj):
        return obj.categories.aggregate(
            total=Count('tests')
        )['total'] or 0
    test_count.short_description = 'Total Tests'


@admin.register(TestCategory)
class TestCategoryAdmin(admin.ModelAdmin):
    list_display = ('section', 'name', 'display_order', 'test_count', 'is_active')
    list_filter = ('section', 'is_active')
    search_fields = ('name', 'description')
    ordering = ('section', 'display_order', 'name')
    
    def test_count(self, obj):
        return obj.tests.count()
    test_count.short_description = 'Tests'


@admin.register(LabTest)
class LabTestAdmin(admin.ModelAdmin):
    list_display = (
        'test_code', 'name', 'category', 'sample_type', 'price', 
        'reporting_time_hours', 'requires_fasting', 'is_active'
    )
    list_filter = (
        'category__section', 'category', 'sample_type', 
        'requires_fasting', 'is_active'
    )
    search_fields = ('name', 'test_code', 'description')
    readonly_fields = ('test_code',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('test_code', 'name', 'description', 'category')
        }),
        ('Sample Information', {
            'fields': ('sample_type', 'sample_volume', 'collection_instructions')
        }),
        ('Pricing and Time', {
            'fields': ('price', 'reporting_time_hours')
        }),
        ('Reference Values', {
            'fields': ('reference_range_male', 'reference_range_female', 'reference_range_child', 'units')
        }),
        ('Settings', {
            'fields': ('is_active', 'requires_fasting', 'created_by')
        })
    )


@admin.register(LabOrder)
class LabOrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number', 'patient_name', 'doctor', 'priority', 
        'status', 'total_amount', 'is_paid', 'order_date'
    )
    list_filter = ('status', 'priority', 'is_paid', 'order_date')
    search_fields = (
        'order_number', 'patient__first_name', 'patient__last_name',
        'doctor__user__first_name', 'doctor__user__last_name'
    )
    readonly_fields = ('order_number',)
    date_hierarchy = 'order_date'
    
    def patient_name(self, obj):
        return obj.patient.get_full_name()
    patient_name.short_description = 'Patient'


@admin.register(LabOrderItem)
class LabOrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'test', 'status', 'price')
    list_filter = ('status', 'order__order_date')
    search_fields = ('test__name', 'order__order_number', 'order__patient__first_name')


@admin.register(LabResult)
class LabResultAdmin(admin.ModelAdmin):
    list_display = (
        'order_info', 'test_name', 'result_value', 'abnormal_flag',
        'status', 'performed_by', 'reviewed_by', 'performed_at'
    )
    list_filter = (
        'status', 'abnormal_flag', 'performed_at', 
        'order_item__test__category__section'
    )
    search_fields = (
        'order_item__order__patient__first_name',
        'order_item__order__patient__last_name',
        'order_item__test__name'
    )
    readonly_fields = ('order_item',)
    date_hierarchy = 'performed_at'
    
    def order_info(self, obj):
        return f"{obj.order_item.order.order_number} - {obj.order_item.order.patient.get_full_name()}"
    order_info.short_description = 'Order - Patient'
    
    def test_name(self, obj):
        return obj.order_item.test.name
    test_name.short_description = 'Test'


@admin.register(LabEquipment)
class LabEquipmentAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'model', 'manufacturer', 'status', 
        'maintenance_status', 'calibration_status', 'location'
    )
    list_filter = ('status', 'manufacturer')
    search_fields = ('name', 'model', 'serial_number')
    filter_horizontal = ('tests',)
    
    def maintenance_status(self, obj):
        if obj.is_maintenance_due():
            return format_html('<span style="color: red;">Due</span>')
        return format_html('<span style="color: green;">OK</span>')
    maintenance_status.short_description = 'Maintenance'
    
    def calibration_status(self, obj):
        if obj.is_calibration_due():
            return format_html('<span style="color: red;">Due</span>')
        return format_html('<span style="color: green;">OK</span>')
    calibration_status.short_description = 'Calibration'


@admin.register(DigitalSignature)
class DigitalSignatureAdmin(admin.ModelAdmin):
    list_display = (
        'lab_result_info', 'signature_type', 'doctor', 
        'signed_at', 'verification_status'
    )
    list_filter = ('signature_type', 'signed_at')
    search_fields = (
        'doctor__user__first_name', 'doctor__user__last_name',
        'lab_result__order_item__order__patient__first_name'
    )
    readonly_fields = ('signature_hash', 'signed_at')
    
    def lab_result_info(self, obj):
        return f"{obj.lab_result.order_item.test.name} - {obj.lab_result.order_item.order.patient.get_full_name()}"
    lab_result_info.short_description = 'Test - Patient'
    
    def verification_status(self, obj):
        # Check if signature hash is valid
        if obj.signature_hash == obj.generate_signature_hash():
            return format_html('<span style="color: green;">Valid</span>')
        return format_html('<span style="color: red;">Invalid</span>')
    verification_status.short_description = 'Verification'


@admin.register(LabReportTemplate)
class LabReportTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'section', 'is_default', 'is_active', 'created_by', 'created_at')
    list_filter = ('section', 'is_default', 'is_active')
    search_fields = ('name', 'description')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'section')
        }),
        ('Template Content', {
            'fields': ('header_html', 'body_html', 'footer_html')
        }),
        ('Styling', {
            'fields': ('css_styles',)
        }),
        ('Settings', {
            'fields': ('is_default', 'is_active', 'signature_positions')
        })
    )
 