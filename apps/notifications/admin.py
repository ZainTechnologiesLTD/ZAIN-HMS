# notifications/admin.py
from django.contrib import admin
from .models import (
    Notification, NotificationTemplate, PatientNotification, 
    NotificationSettings, DeliveryLog
)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'title', 'level', 'read', 'created_at']
    list_filter = ['level', 'read', 'created_at']
    search_fields = ['recipient__username', 'recipient__email', 'title', 'message']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('recipient')


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'document_type', 'channel', 'is_active', 'auto_send']
    list_filter = ['document_type', 'channel', 'is_active', 'auto_send']
    search_fields = ['name', 'subject_template']
    ordering = ['document_type', 'channel']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'document_type', 'channel')
        }),
        ('Template Content', {
            'fields': ('subject_template', 'body_template')
        }),
        ('Settings', {
            'fields': ('is_active', 'auto_send', 'send_delay_minutes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        
        # Add help text for template variables
        template_help = """
        Available template variables:
        {{patient_name}} - Full name of patient
        {{patient_first_name}} - First name of patient  
        {{patient_phone}} - Patient phone number
        {{patient_email}} - Patient email
        {{document_type}} - Type of document
        {{document_url}} - Link to document
        {{hospital_name}} - Hospital name
        {{date}} - Current date
        {{time}} - Current time
        {{invoice_number}} - For bills/invoices
        {{appointment_date}} - For appointments
        {{doctor_name}} - For prescriptions/appointments
        """
        
        form.base_fields['body_template'].help_text = template_help
        return form


class DeliveryLogInline(admin.TabularInline):
    model = DeliveryLog
    readonly_fields = ['attempt_number', 'success', 'error_message', 'timestamp', 'response_status_code']
    extra = 0
    can_delete = False
    
    def has_add_permission(self, request, obj):
        return False


@admin.register(PatientNotification)
class PatientNotificationAdmin(admin.ModelAdmin):
    list_display = ['patient', 'template', 'status', 'scheduled_at', 'sent_at', 'retry_count']
    list_filter = ['status', 'template__channel', 'template__document_type', 'scheduled_at']
    search_fields = ['patient__first_name', 'patient__last_name', 'subject']
    readonly_fields = ['id', 'created_at', 'updated_at', 'sent_at', 'delivered_at', 'read_at', 'failed_at']
    ordering = ['-created_at']
    inlines = [DeliveryLogInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'patient', 'template', 'status')
        }),
        ('Document Reference', {
            'fields': ('content_type', 'object_id', 'document_url', 'attachment_path')
        }),
        ('Recipients', {
            'fields': ('recipient_email', 'recipient_phone', 'recipient_whatsapp', 'recipient_telegram')
        }),
        ('Content', {
            'fields': ('subject', 'message_body'),
            'classes': ('collapse',)
        }),
        ('Delivery Tracking', {
            'fields': ('scheduled_at', 'sent_at', 'delivered_at', 'read_at', 'failed_at')
        }),
        ('Error Handling', {
            'fields': ('error_message', 'retry_count', 'max_retries'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('delivery_provider', 'external_message_id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'patient', 'template', 'content_type'
        )
    
    actions = ['retry_failed_notifications', 'mark_as_cancelled']
    
    def retry_failed_notifications(self, request, queryset):
        """Retry failed notifications"""
        failed_notifications = queryset.filter(status='FAILED')
        count = 0
        
        for notification in failed_notifications:
            if notification.retry_count < notification.max_retries:
                notification.status = 'PENDING'
                notification.error_message = ''
                notification.save()
                count += 1
        
        self.message_user(request, f"Queued {count} notifications for retry.")
    
    retry_failed_notifications.short_description = "Retry selected failed notifications"
    
    def mark_as_cancelled(self, request, queryset):
        """Mark notifications as cancelled"""
        count = queryset.exclude(status__in=['SENT', 'DELIVERED']).update(status='CANCELLED')
        self.message_user(request, f"Cancelled {count} notifications.")
    
    mark_as_cancelled.short_description = "Cancel selected notifications"


@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    
    fieldsets = (
        ('Email Settings', {
            'fields': ('email_enabled', 'email_from_name', 'email_from_address')
        }),
        ('WhatsApp Settings', {
            'fields': ('whatsapp_enabled', 'whatsapp_api_url', 'whatsapp_api_key', 'whatsapp_phone_number'),
            'description': 'Configure WhatsApp Business API for document delivery'
        }),
        ('Telegram Settings', {
            'fields': ('telegram_enabled', 'telegram_bot_token', 'telegram_chat_id'),
            'description': 'Configure Telegram Bot for document delivery'
        }),
        ('SMS Settings', {
            'fields': ('sms_enabled', 'sms_api_url', 'sms_api_key', 'sms_sender_id'),
            'description': 'Configure SMS service for notifications'
        }),
        ('General Settings', {
            'fields': ('document_base_url', 'auto_cleanup_days')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def has_add_permission(self, request):
        # Only allow one settings instance
        return not NotificationSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of settings
        return False


@admin.register(DeliveryLog)
class DeliveryLogAdmin(admin.ModelAdmin):
    list_display = ['notification', 'attempt_number', 'success', 'timestamp']
    list_filter = ['success', 'timestamp', 'response_status_code']
    search_fields = ['notification__patient__first_name', 'notification__patient__last_name']
    readonly_fields = ['timestamp']
    ordering = ['-timestamp']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('notification', 'attempt_number', 'success', 'timestamp')
        }),
        ('Request Details', {
            'fields': ('api_endpoint', 'request_payload'),
            'classes': ('collapse',)
        }),
        ('Response Details', {
            'fields': ('response_status_code', 'response_body'),
            'classes': ('collapse',)
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'notification', 'notification__patient'
        )
    
    def has_add_permission(self, request):
        # Delivery logs are created automatically
        return False
    
    def has_change_permission(self, request, obj=None):
        # Delivery logs should not be modified
        return False
