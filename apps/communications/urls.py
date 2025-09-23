# Communications URL configuration
from django.urls import path
from . import views
from .webhooks import (
    WhatsAppWebhookView, TelegramWebhookView, 
    email_webhook, sms_webhook, webhook_verification
)

app_name = 'communications'

urlpatterns = [
    # Dashboard
    path('', views.communications_dashboard, name='dashboard'),
    
    # API endpoints
    path('api/track/', views.track_communication, name='track_communication'),
    path('api/bulk/', views.bulk_communication, name='bulk_communication'),
    path('api/status/<int:log_id>/', views.update_communication_status, name='update_status'),
    
    # Views
    path('history/', views.communication_history, name='history'),
    path('history/<uuid:appointment_id>/', views.communication_history, name='appointment_history'),
    
    # Template Management (Custom interface for hospital admins)
    path('templates/', views.template_list, name='template_list'),
    path('templates/create/', views.template_create, name='template_create'),
    path('templates/<int:template_id>/', views.template_detail, name='template_detail'),
    path('templates/<int:template_id>/edit/', views.template_edit, name='template_edit'),
    
    # Webhook endpoints for delivery status
    path('webhooks/whatsapp/', WhatsAppWebhookView.as_view(), name='whatsapp_webhook'),
    path('webhooks/telegram/', TelegramWebhookView.as_view(), name='telegram_webhook'),
    path('webhooks/email/', email_webhook, name='email_webhook'),
    path('webhooks/sms/', sms_webhook, name='sms_webhook'),
    
    # Webhook verification endpoints
    path('webhooks/verify/<str:provider>/', webhook_verification, name='webhook_verification'),
]
