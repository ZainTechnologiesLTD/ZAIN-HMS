# apps/core/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Notification, ActivityLog, SystemConfiguration, 
    FileUpload, SystemSetting, HospitalModule
)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
    'title', 'recipient', 'type', 'priority', 'is_read', 
    'created_at'
    ]
    list_filter = [
    'type', 'priority', 'is_read', 'created_at'
    ]
    search_fields = [
        'title', 'message', 'recipient__first_name', 'recipient__last_name',
        'recipient__email'
    ]
    readonly_fields = ['created_at', 'read_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('recipient', 'sender')
        }),
        ('Notification Details', {
            'fields': ('type', 'priority', 'title', 'message', 'link', 'data')
        }),
        ('Status', {
            'fields': ('is_read', 'read_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # ZAIN HMS unified system - show all
        return qs


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'action', 'model_name', 'object_repr', 
        'ip_address', 'timestamp'
    ]
    list_filter = [
        'action', 'model_name', 'timestamp'
    ]
    search_fields = [
        'user__first_name', 'user__last_name', 'user__email',
        'model_name', 'object_repr', 'ip_address'
    ]
    readonly_fields = [
        'user', 'action', 'model_name', 'object_id', 'object_repr',
        'changes', 'ip_address', 'user_agent', 'timestamp'
    ]
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # ZAIN HMS unified system - show all
        return qs


@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    list_display = [
        'system_name', 'contact_email', 'currency_code',
        'appointment_duration', 'updated_at'
    ]
    search_fields = ['system_name', 'contact_email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('System Information', {
            'fields': (
                'system_name', 'system_logo',
                'contact_email', 'contact_phone', 'address'
            )
        }),
        ('Business Settings', {
            'fields': (
                'consultation_fee', 'currency_code', 'tax_rate'
            )
        }),
        ('Appointment Settings', {
            'fields': (
                'appointment_duration', 'advance_booking_days', 'cancellation_hours'
            )
        }),
        ('Patient Settings', {
            'fields': (
                'patient_id_prefix', 'auto_generate_patient_id'
            )
        }),
        ('Notifications', {
            'fields': (
                'email_notifications', 'sms_notifications', 'whatsapp_notifications'
            )
        }),
        ('Backup Settings', {
            'fields': (
                'auto_backup', 'backup_frequency'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # ZAIN HMS unified system - show all
        return qs
    
    def has_add_permission(self, request):
        # Only superusers can add system configurations
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete system configurations
        return request.user.is_superuser


@admin.register(FileUpload)
class FileUploadAdmin(admin.ModelAdmin):
    list_display = [
        'original_name', 'uploaded_by', 'formatted_file_size', 
        'content_type', 'is_public', 'created_at'
    ]
    list_filter = [
        'content_type', 'is_public', 'created_at'
    ]
    search_fields = [
        'original_name', 'description', 
        'uploaded_by__first_name', 'uploaded_by__last_name'
    ]
    readonly_fields = [
        'file_size', 'content_type', 'uploaded_by', 'created_at',
        'formatted_file_size', 'file_preview'
    ]
    
    def formatted_file_size(self, obj):
        """Display human-readable file size"""
        size = obj.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    formatted_file_size.short_description = 'File Size'
    
    def file_preview(self, obj):
        """Show file preview if it's an image"""
        if obj.content_type.startswith('image/'):
            return format_html(
                '<img src="{}" width="200" height="150" style="object-fit: cover;" />',
                obj.file.url
            )
        else:
            return format_html(
                '<a href="{}" target="_blank">Download File</a>',
                obj.file.url
            )
    file_preview.short_description = 'Preview'
    
    def get_queryset(self, request):
        return super().get_queryset(request)
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set on creation
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ['key', 'value_preview', 'is_active', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['key', 'value', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    def value_preview(self, obj):
        """Show truncated value"""
        return (obj.value[:50] + '...') if len(obj.value) > 50 else obj.value
    value_preview.short_description = 'Value'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Filter by user's tenant if not superuser
        if hasattr(request.user, 'tenant') and request.user.tenant:
            return qs.filter(tenant=request.user.tenant)
        return qs.none()


# Customize admin site - ZAIN HMS Unified System
admin.site.site_header = "ZAIN HMS - Hospital Management System"
admin.site.site_title = "ZAIN HMS Administration"  
admin.site.index_title = "Welcome to ZAIN Hospital Management System - Unified Healthcare Platform"


@admin.register(HospitalModule)
class HospitalModuleAdmin(admin.ModelAdmin):
    """Admin interface for Hospital Modules"""
    list_display = ['name', 'module_type', 'is_premium', 'monthly_cost', 'is_active', 'version']
    list_filter = ['is_premium', 'is_active', 'module_type', 'created_at']
    search_fields = ['name', 'module_type', 'description']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'module_type', 'description', 'icon', 'version')
        }),
        ('Pricing & Features', {
            'fields': ('is_premium', 'monthly_cost', 'features'),
            'classes': ('collapse',)
        }),
        ('Dependencies', {
            'fields': ('required_modules',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        })
    )
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Make features field a textarea for better editing
        if 'features' in form.base_fields:
            form.base_fields['features'].help_text = "Enter features as JSON list, e.g., ['Feature 1', 'Feature 2']"
        return form
