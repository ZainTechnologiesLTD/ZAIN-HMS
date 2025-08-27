"""
Enhanced Admin Configuration for Zain HMS
Provides additional functionality and customizations for the admin interface
"""

from django.contrib import admin
from django.contrib.admin import AdminSite
from django.db.models import Sum, Count, Q
from django.utils.html import format_html, format_html_join
from django.urls import path, reverse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.template.response import TemplateResponse
from django.http import JsonResponse, HttpResponse
from django.core.cache import cache
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from datetime import datetime, timedelta
import json
import csv


class EnhancedAdminMixin:
    """Mixin to add common enhanced functionality to admin classes."""
    
    def get_queryset(self, request):
        """Optimize queryset with select_related and prefetch_related."""
        qs = super().get_queryset(request)
        # Add common optimizations here
        return qs
    
    def get_list_display_links(self, request, list_display):
        """Enhance list display links."""
        if list_display and hasattr(self.model, 'get_absolute_url'):
            return [list_display[0]]  # Make first column clickable
        return super().get_list_display_links(request, list_display)
    
    def get_actions(self, request):
        """Add custom actions."""
        actions = super().get_actions(request)
        if hasattr(self, 'custom_actions'):
            for action_name in self.custom_actions:
                actions[action_name] = (
                    getattr(self, action_name),
                    action_name,
                    getattr(self, action_name).short_description
                )
        return actions


class ExportCSVMixin:
    """Mixin to add CSV export functionality."""
    
    def export_as_csv(self, request, queryset):
        """Export selected items as CSV."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename={self.model._meta.model_name}_export.csv'
        
        writer = csv.writer(response)
        
        # Write headers
        field_names = []
        for field in self.list_display:
            if hasattr(self.model, field):
                field_names.append(self.model._meta.get_field(field).verbose_name)
            else:
                field_names.append(field.replace('_', ' ').title())
        writer.writerow(field_names)
        
        # Write data
        for obj in queryset:
            row = []
            for field in self.list_display:
                if hasattr(obj, field):
                    value = getattr(obj, field)
                    if callable(value):
                        value = value()
                    row.append(str(value))
                else:
                    row.append('')
            writer.writerow(row)
        
        self.message_user(
            request,
            f"Successfully exported {queryset.count()} {self.model._meta.verbose_name_plural}."
        )
        
        return response
    
    export_as_csv.short_description = "Export selected items as CSV"


class AdvancedFiltersMixin:
    """Mixin to add advanced filtering capabilities."""
    
    def get_list_filter(self, request):
        """Add dynamic filters based on user permissions."""
        filters = list(self.list_filter or [])
        
        # Add common filters for models with certain fields
        if hasattr(self.model, 'is_active'):
            if 'is_active' not in filters:
                filters.append('is_active')
        
        if hasattr(self.model, 'created_at'):
            if 'created_at' not in filters:
                filters.append(('created_at', admin.DateFieldListFilter))
        
        return filters


class BulkActionsMixin:
    """Mixin to add common bulk actions."""
    
    def make_active(self, request, queryset):
        """Bulk activate selected items."""
        if hasattr(self.model, 'is_active'):
            updated = queryset.update(is_active=True)
            self.message_user(
                request,
                f"Successfully activated {updated} {self.model._meta.verbose_name_plural}."
            )
    make_active.short_description = "Mark selected items as active"
    
    def make_inactive(self, request, queryset):
        """Bulk deactivate selected items."""
        if hasattr(self.model, 'is_active'):
            updated = queryset.update(is_active=False)
            self.message_user(
                request,
                f"Successfully deactivated {updated} {self.model._meta.verbose_name_plural}."
            )
    make_inactive.short_description = "Mark selected items as inactive"


class EnhancedModelAdmin(
    EnhancedAdminMixin,
    ExportCSVMixin,
    AdvancedFiltersMixin,
    BulkActionsMixin,
    admin.ModelAdmin
):
    """Enhanced ModelAdmin with all mixins."""
    
    # Common configuration
    list_per_page = 25
    list_max_show_all = 100
    save_on_top = True
    preserve_filters = True
    
    # Add export action by default
    actions = ['export_as_csv']
    
    # Add bulk actions if model has is_active field
    def get_actions(self, request):
        actions = super().get_actions(request)
        if hasattr(self.model, 'is_active'):
            actions['make_active'] = (
                self.make_active,
                'make_active',
                self.make_active.short_description
            )
            actions['make_inactive'] = (
                self.make_inactive,
                'make_inactive', 
                self.make_inactive.short_description
            )
        return actions
    
    def get_readonly_fields(self, request, obj=None):
        """Make certain fields readonly for non-superusers."""
        readonly_fields = list(self.readonly_fields or [])
        
        # Add common readonly fields
        if hasattr(self.model, 'created_at') and 'created_at' not in readonly_fields:
            readonly_fields.append('created_at')
        if hasattr(self.model, 'updated_at') and 'updated_at' not in readonly_fields:
            readonly_fields.append('updated_at')
        if hasattr(self.model, 'created_by') and 'created_by' not in readonly_fields:
            readonly_fields.append('created_by')
        
        return readonly_fields
    
    def save_model(self, request, obj, form, change):
        """Enhanced save method."""
        # Set created_by for new objects
        if not change and hasattr(obj, 'created_by') and not obj.created_by:
            obj.created_by = request.user
        
        # Set updated_by for existing objects
        if change and hasattr(obj, 'updated_by'):
            obj.updated_by = request.user
        
        super().save_model(request, obj, form, change)


class DashboardWidgetMixin:
    """Mixin to add dashboard widgets for admin."""
    
    def get_dashboard_stats(self):
        """Override in subclasses to provide model-specific stats."""
        return {}
    
    def changelist_view(self, request, extra_context=None):
        """Add dashboard stats to changelist."""
        extra_context = extra_context or {}
        extra_context['dashboard_stats'] = self.get_dashboard_stats()
        return super().changelist_view(request, extra_context)


# Custom admin actions
def export_to_json(modeladmin, request, queryset):
    """Export selected objects to JSON."""
    from django.core import serializers
    
    response = HttpResponse(content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename={modeladmin.model._meta.model_name}_export.json'
    
    data = serializers.serialize('json', queryset, indent=2)
    response.write(data)
    
    modeladmin.message_user(
        request,
        f"Successfully exported {queryset.count()} items as JSON."
    )
    
    return response

export_to_json.short_description = "Export selected items as JSON"


def duplicate_selected(modeladmin, request, queryset):
    """Duplicate selected objects."""
    duplicated = 0
    
    for obj in queryset:
        # Create a copy
        obj.pk = None
        obj.save()
        duplicated += 1
    
    modeladmin.message_user(
        request,
        f"Successfully duplicated {duplicated} {modeladmin.model._meta.verbose_name_plural}."
    )

duplicate_selected.short_description = "Duplicate selected items"


# Enhanced admin filters
class ActiveStatusFilter(admin.SimpleListFilter):
    """Filter for active/inactive status."""
    title = 'Status'
    parameter_name = 'status'
    
    def lookups(self, request, model_admin):
        return (
            ('active', 'Active'),
            ('inactive', 'Inactive'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'active':
            return queryset.filter(is_active=True)
        if self.value() == 'inactive':
            return queryset.filter(is_active=False)
        return queryset


class DateRangeFilter(admin.SimpleListFilter):
    """Filter for date ranges."""
    title = 'Date Range'
    parameter_name = 'date_range'
    
    def lookups(self, request, model_admin):
        return (
            ('today', 'Today'),
            ('yesterday', 'Yesterday'),
            ('week', 'This Week'),
            ('month', 'This Month'),
            ('year', 'This Year'),
        )
    
    def queryset(self, request, queryset):
        today = datetime.now().date()
        
        if self.value() == 'today':
            return queryset.filter(created_at__date=today)
        elif self.value() == 'yesterday':
            yesterday = today - timedelta(days=1)
            return queryset.filter(created_at__date=yesterday)
        elif self.value() == 'week':
            week_start = today - timedelta(days=today.weekday())
            return queryset.filter(created_at__date__gte=week_start)
        elif self.value() == 'month':
            return queryset.filter(
                created_at__year=today.year,
                created_at__month=today.month
            )
        elif self.value() == 'year':
            return queryset.filter(created_at__year=today.year)
        
        return queryset


# Custom admin widgets for better UX
class ColorizedStatusWidget:
    """Helper to colorize status fields in admin."""
    
    @staticmethod
    def colorize_status(status, obj=None):
        """Return colorized HTML for status."""
        colors = {
            'active': 'green',
            'inactive': 'red',
            'pending': 'orange',
            'completed': 'blue',
            'cancelled': 'gray',
        }
        
        color = colors.get(status.lower(), 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            status.title()
        )
    
    @staticmethod 
    def boolean_icon(value):
        """Return icon for boolean values."""
        if value:
            return format_html(
                '<i class="fas fa-check-circle" style="color: green;" title="Yes"></i>'
            )
        else:
            return format_html(
                '<i class="fas fa-times-circle" style="color: red;" title="No"></i>'
            )


# Utility functions for admin customization
def admin_changelist_link(attr, short_description, empty_description="-"):
    """
    Decorator for creating links in admin changelist.
    Usage: @admin_changelist_link('related_field', 'Related Objects')
    """
    def wrap(func):
        def field_func(self, obj):
            related_obj = getattr(obj, attr)
            if related_obj is None:
                return empty_description
            url = reverse(f'admin:{related_obj._meta.app_label}_{related_obj._meta.model_name}_changelist')
            return format_html('<a href="{}">{}</a>', url, func(self, obj))
        field_func.short_description = short_description
        field_func.allow_tags = True
        return field_func
    return wrap


def admin_change_link(attr, short_description, empty_description="-"):
    """
    Decorator for creating edit links in admin.
    Usage: @admin_change_link('related_field', 'Edit Related')
    """
    def wrap(func):
        def field_func(self, obj):
            related_obj = getattr(obj, attr)
            if related_obj is None:
                return empty_description
            url = reverse(f'admin:{related_obj._meta.app_label}_{related_obj._meta.model_name}_change', args=[related_obj.pk])
            return format_html('<a href="{}">{}</a>', url, func(self, obj))
        field_func.short_description = short_description
        field_func.allow_tags = True
        return field_func
    return wrap


# Enhanced admin site with custom dashboard
class ZainHMSAdminSite(AdminSite):
    """Custom admin site with enhanced features."""
    
    site_header = 'Zain HMS Administration'
    site_title = 'Zain HMS Admin'
    index_title = 'Hospital Management Dashboard'
    site_url = '/'
    enable_nav_sidebar = True
    
    def get_urls(self):
        """Add custom admin URLs."""
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.dashboard_view), name='dashboard'),
            path('analytics/', self.admin_view(self.analytics_view), name='analytics'),
            path('api/stats/', self.admin_view(self.stats_api), name='stats_api'),
        ]
        return custom_urls + urls
    
    def dashboard_view(self, request):
        """Custom dashboard view."""
        context = {
            'title': 'Enhanced Dashboard',
            'site_header': self.site_header,
        }
        return TemplateResponse(request, 'admin/dashboard.html', context)
    
    def analytics_view(self, request):
        """Analytics view."""
        context = {
            'title': 'Analytics',
            'site_header': self.site_header,
        }
        return TemplateResponse(request, 'admin/analytics.html', context)
    
    def stats_api(self, request):
        """API endpoint for dashboard stats."""
        # This would be populated with real data
        stats = {
            'patients': {'total': 1250, 'new_today': 12},
            'appointments': {'total': 89, 'completed_today': 45},
            'revenue': {'today': 15000, 'month': 450000},
            'staff': {'doctors': 24, 'nurses': 67, 'admin': 12}
        }
        return JsonResponse(stats)


# Create enhanced admin site instance
enhanced_admin_site = ZainHMSAdminSite(name='enhanced_admin')


# Monkey patch to enhance existing admin classes
def enhance_existing_admin():
    """Apply enhancements to existing registered admin classes."""
    for model, admin_class in admin.site._registry.items():
        # Add export action if not present
        if hasattr(admin_class, 'actions'):
            if 'export_as_csv' not in admin_class.actions:
                admin_class.actions = list(admin_class.actions) + ['export_as_csv']
        else:
            admin_class.actions = ['export_as_csv']
        
        # Add export method to admin class
        if not hasattr(admin_class, 'export_as_csv'):
            admin_class.export_as_csv = ExportCSVMixin.export_as_csv


# Apply enhancements on import
enhance_existing_admin()
