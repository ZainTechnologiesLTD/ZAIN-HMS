# apps/radiology/admin.py
from django.contrib import admin
from .models import (
    StudyType, RadiologyOrder, RadiologyOrderItem, 
    ImagingStudy, ImagingImage, RadiologyEquipment
)


@admin.register(StudyType)
class StudyTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'modality', 'price', 'is_active', 'created_at']
    list_filter = ['modality', 'is_active', 'created_at']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'description', 'modality')
        }),
        ('Pricing & Duration', {
            'fields': ('price', 'estimated_duration')
        }),
        ('Clinical Details', {
            'fields': ('preparation_instructions', 'contrast_required')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('System Information', {
            'fields': ('hospital', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


class RadiologyOrderItemInline(admin.TabularInline):
    model = RadiologyOrderItem
    extra = 1
    fields = ['study_type', 'quantity', 'notes']


@admin.register(RadiologyOrder)
class RadiologyOrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'patient', 'ordering_doctor', 
        'status', 'priority', 'created_at'
    ]
    list_filter = ['status', 'priority', 'created_at']
    search_fields = [
        'order_number', 'patient__patient_id', 'patient__first_name', 
        'patient__last_name', 'ordering_doctor__first_name', 'ordering_doctor__last_name'
    ]
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    inlines = [RadiologyOrderItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'patient', 'ordering_doctor')
        }),
        ('Clinical Details', {
            'fields': ('clinical_indication', 'priority')
        }),
        ('Scheduling', {
            'fields': ('scheduled_date', 'status')
        }),
        ('Additional Information', {
            'fields': ('special_instructions',)
        }),
        ('System Information', {
            'fields': ('hospital', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


class ImagingImageInline(admin.TabularInline):
    model = ImagingImage
    extra = 1
    fields = ['description', 'sequence_number', 'dicom_file', 'image_file']


@admin.register(ImagingStudy)
class ImagingStudyAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'order_item', 'modality', 'study_date', 
        'status'
    ]
    list_filter = ['modality', 'status', 'study_date']
    search_fields = [
        'order_item__order__order_number', 
        'order_item__order__patient__patient_id'
    ]
    readonly_fields = ['id']
    inlines = [ImagingImageInline]
    
    fieldsets = (
        ('Study Information', {
            'fields': ('id', 'order_item', 'study_date', 'modality')
        }),
        ('Procedure Details', {
            'fields': ('body_part', 'technique')
        }),
        ('Contrast Information', {
            'fields': ('contrast_used', 'contrast_agent')
        }),
        ('Results', {
            'fields': ('findings', 'impression', 'recommendations', 'status')
        }),
        ('Quality Assessment', {
            'fields': ('study_quality',)
        }),
        ('Personnel', {
            'fields': ('reported_by', 'reported_at')
        })
    )


@admin.register(RadiologyEquipment)
class RadiologyEquipmentAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'manufacturer', 'model', 'equipment_type', 
        'status', 'room_number'
    ]
    list_filter = ['equipment_type', 'status', 'manufacturer']
    search_fields = ['name', 'manufacturer', 'model', 'serial_number']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Equipment Information', {
            'fields': ('name', 'manufacturer', 'model', 'serial_number')
        }),
        ('Technical Details', {
            'fields': ('equipment_type', 'status', 'room_number', 'location_description')
        }),
        ('Maintenance', {
            'fields': ('installation_date', 'last_maintenance', 'next_maintenance')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ImagingImage)
class ImagingImageAdmin(admin.ModelAdmin):
    list_display = ['study', 'description', 'series_number', 'instance_number', 'created_at']
    list_filter = ['study__modality', 'created_at']
    search_fields = ['study__id', 'description']
    readonly_fields = ['created_at']
