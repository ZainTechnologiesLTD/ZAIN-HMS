from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import CommunicationLog, CommunicationTemplate, PatientCommunicationPreference


@admin.register(CommunicationTemplate)
class CommunicationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'channel', 'template_type', 'is_active', 'created_at', 'usage_count']
    list_filter = ['channel', 'template_type', 'is_active', 'created_at']
    search_fields = ['name', 'subject_template', 'message_template']
    readonly_fields = ['created_at', 'updated_at', 'usage_count']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'channel', 'template_type', 'is_active')
        }),
        ('Content', {
            'fields': ('subject_template', 'message_template'),
            'description': 'Use {patient_name}, {appointment_date}, {appointment_time}, {doctor_name}, {hospital_name} for dynamic content'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'usage_count'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _usage_count=Count('communicationlog')
        )
        return queryset
    
    def usage_count(self, obj):
        count = getattr(obj, '_usage_count', 0)
        if count > 0:
            url = reverse('admin:communications_communicationlog_changelist')
            return format_html(
                '<a href="{}?template__id__exact={}">{} uses</a>',
                url, obj.pk, count
            )
        return '0 uses'
    usage_count.short_description = 'Usage Count'
    usage_count.admin_order_field = '_usage_count'


@admin.register(CommunicationLog)
class CommunicationLogAdmin(admin.ModelAdmin):
    list_display = [
        'appointment_link', 'patient_name', 'channel', 'status_badge', 
        'sent_at', 'delivered_at', 'error_message_short'
    ]
    list_filter = [
        'channel', 'status', 'sent_at', 'delivered_at',
        ('appointment__hospital', admin.RelatedOnlyFieldListFilter),
        ('appointment__doctor', admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = [
        'appointment__patient__first_name',
        'appointment__patient__last_name', 
        'appointment__patient__phone',
        'recipient_phone', 'recipient_email',
        'message_content'
    ]
    readonly_fields = [
        'sent_at', 'delivered_at', 'read_at', 'failed_at',
        'message_preview', 'response_data_formatted'
    ]
    
    fieldsets = (
        ('Communication Details', {
            'fields': ('appointment', 'channel', 'template', 'status')
        }),
        ('Recipient Information', {
            'fields': ('recipient_phone', 'recipient_email')
        }),
        ('Message Content', {
            'fields': ('subject', 'message_preview')
        }),
        ('Delivery Tracking', {
            'fields': ('sent_at', 'delivered_at', 'read_at', 'failed_at')
        }),
        ('Error Information', {
            'fields': ('error_message', 'response_data_formatted'),
            'classes': ('collapse',)
        })
    )
    
    def appointment_link(self, obj):
        if obj.appointment:
            url = reverse('admin:appointments_appointment_change', args=[obj.appointment.pk])
            return format_html(
                '<a href="{}">{}</a>',
                url, str(obj.appointment)
            )
        return '-'
    appointment_link.short_description = 'Appointment'
    
    def patient_name(self, obj):
        if obj.appointment and obj.appointment.patient:
            return obj.appointment.patient.get_full_name()
        return '-'
    patient_name.short_description = 'Patient'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',    # warning
            'sent': '#17a2b8',       # info
            'delivered': '#28a745',  # success
            'read': '#6f42c1',       # purple
            'failed': '#dc3545',     # danger
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_status_display().upper()
        )
    status_badge.short_description = 'Status'
    
    def error_message_short(self, obj):
        if obj.error_message:
            return obj.error_message[:50] + ('...' if len(obj.error_message) > 50 else '')
        return '-'
    error_message_short.short_description = 'Error'
    
    def message_preview(self, obj):
        if obj.message:
            preview = obj.message[:200] + ('...' if len(obj.message) > 200 else '')
            return format_html('<div style="max-width: 400px; white-space: pre-wrap;">{}</div>', preview)
        return '-'
    message_preview.short_description = 'Message Preview'
    
    def response_data_formatted(self, obj):
        if obj.response_data:
            import json
            try:
                formatted = json.dumps(obj.response_data, indent=2)
                return format_html('<pre style="background: #f8f9fa; padding: 10px; border-radius: 4px;">{}</pre>', formatted)
            except:
                return str(obj.response_data)
        return '-'
    response_data_formatted.short_description = 'Response Data'


@admin.register(PatientCommunicationPreference)
class PatientCommunicationPreferenceAdmin(admin.ModelAdmin):
    list_display = [
        'patient_name', 'allow_whatsapp', 'allow_telegram', 
        'allow_viber', 'allow_email', 'allow_sms', 'updated_at'
    ]
    list_filter = [
        'allow_whatsapp', 'allow_telegram', 'allow_viber', 
        'allow_email', 'allow_sms', 'updated_at'
    ]
    search_fields = [
        'patient__first_name', 'patient__last_name', 
        'patient__phone', 'patient__email'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Patient Information', {
            'fields': ('patient',)
        }),
        ('Communication Preferences', {
            'fields': (
                'allow_whatsapp', 'allow_telegram', 'allow_viber',
                'allow_email', 'allow_sms', 'allow_voice'
            )
        }),
        ('Timing & Language', {
            'fields': (
                'preferred_time_start', 'preferred_time_end', 'timezone',
                'preferred_language'
            )
        }),
        ('Reminder Settings', {
            'fields': (
                'reminder_advance_hours', 'send_confirmation',
                'send_reminder', 'send_follow_up'
            )
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def patient_name(self, obj):
        return obj.patient.get_full_name()
    patient_name.short_description = 'Patient Name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('patient')


# Admin site customization removed - handled by core app
