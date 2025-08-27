# apps/reports/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Report, ReportTemplate


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'report_type', 'format', 'status', 'generated_by', 
        'total_records', 'created_at'
    ]
    list_filter = ['report_type', 'format', 'status', 'created_at']
    search_fields = ['name', 'generated_by__first_name', 'generated_by__last_name']
    readonly_fields = [
        'generated_by', 'total_records', 'file_size', 'created_at', 
        'completed_at', 'error_message'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('generated_by', 'name', 'report_type', 'format')
        }),
        ('Date Range', {
            'fields': ('date_from', 'date_to')
        }),
        ('Filters', {
            'fields': ('filters',),
            'classes': ('collapse',)
        }),
        ('Status & Results', {
            'fields': ('status', 'file', 'total_records', 'file_size', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'report_type', 'is_active', 'created_by', 'created_at'
    ]
    list_filter = ['report_type', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'created_by__first_name']
    readonly_fields = ['created_by', 'created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('created_by', 'name', 'report_type', 'description', 'is_active')
        }),
        ('Template Configuration', {
            'fields': ('columns', 'default_filters', 'chart_config'),
            'classes': ('collapse',)
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
        return qs
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
