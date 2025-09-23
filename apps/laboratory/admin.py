from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Avg
from .models import (
    LabSection, LabTest, LabOrder, LabOrderItem, 
    LabReport, LabEquipment, LabQualityControl, 
    LabSupply, LabSupplyBatch
)


@admin.register(LabSection)
class LabSectionAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'head_of_section', 'requires_digital_signature', 'is_active', 'test_count')
    list_filter = ('is_active', 'requires_digital_signature')
    search_fields = ('name', 'code', 'description')
    
    def test_count(self, obj):
        return obj.tests.count()
    test_count.short_description = 'Tests'


@admin.register(LabTest)
class LabTestAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'section', 'selling_price', 'is_active')
    list_filter = ('section', 'is_active', 'requires_fasting')
    search_fields = ('name', 'code', 'description')
    list_editable = ('selling_price',)


@admin.register(LabOrder)
class LabOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'patient', 'doctor', 'status', 'priority', 'order_date')
    list_filter = ('status', 'priority', 'order_date')
    search_fields = ('order_number', 'patient__first_name', 'patient__last_name', 'doctor__user__first_name')
    readonly_fields = ('order_number', 'total_amount', 'net_amount')


@admin.register(LabOrderItem)
class LabOrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'test', 'result_value', 'is_abnormal', 'is_critical')
    list_filter = ('is_abnormal', 'is_critical', 'test__section')


@admin.register(LabReport)
class LabReportAdmin(admin.ModelAdmin):
    list_display = ('report_number', 'order', 'generated_at', 'generated_by', 'reviewed_by')
    list_filter = ('generated_at', 'delivery_method')
    search_fields = ('report_number', 'order__order_number')


@admin.register(LabEquipment)
class LabEquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'model', 'serial_number', 'is_operational', 'location')
    list_filter = ('is_operational', 'manufacturer')
    search_fields = ('name', 'model', 'serial_number')


@admin.register(LabQualityControl)
class LabQualityControlAdmin(admin.ModelAdmin):
    list_display = ('test', 'control_date', 'is_within_range', 'performed_by')
    list_filter = ('is_within_range', 'control_date')
    search_fields = ('test__name', 'control_lot')


@admin.register(LabSupply)
class LabSupplyAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'current_stock', 'minimum_stock', 'is_low_stock', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'code')
    
    def is_low_stock(self, obj):
        return obj.is_low_stock
    is_low_stock.boolean = True
    is_low_stock.short_description = 'Low Stock'


@admin.register(LabSupplyBatch)
class LabSupplyBatchAdmin(admin.ModelAdmin):
    list_display = ('supply', 'batch_number', 'quantity', 'expiry_date', 'is_expired', 'expires_soon')
    list_filter = ('expiry_date', 'is_active')
    
    def is_expired(self, obj):
        return obj.is_expired
    is_expired.boolean = True
    
    def expires_soon(self, obj):
        return obj.expires_soon
    expires_soon.boolean = True