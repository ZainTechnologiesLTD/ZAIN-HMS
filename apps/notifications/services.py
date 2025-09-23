# apps/notifications/services.py
import requests
import logging
from django.core.mail import EmailMessage
from django.template import Template, Context
from django.conf import settings
from django.utils import timezone
from .models import NotificationSettings, PatientNotification, DeliveryLog, NotificationTemplate
from typing import Dict, Any, Optional
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

logger = logging.getLogger(__name__)


class NotificationService:
    """Base service for sending notifications"""
    
    def __init__(self):
        self._settings = None
    
    @property
    def settings(self):
        """Lazy load settings to avoid database access during app initialization"""
        if self._settings is None:
            self._settings = self._get_settings()
        return self._settings
    
    def _get_settings(self) -> Optional[NotificationSettings]:
        """Get notification settings"""
        try:
            return NotificationSettings.objects.first()
        except (NotificationSettings.DoesNotExist, Exception) as e:
            logger.warning(f"No notification settings found or database not ready: {e}")
            return None
    
    def render_template(self, template_string: str, context: Dict[str, Any]) -> str:
        """Render Django template string with context"""
        template = Template(template_string)
        return template.render(Context(context))
    
    def get_document_context(self, patient_notification: PatientNotification) -> Dict[str, Any]:
        """Get context for template rendering"""
        patient = patient_notification.patient
        document = patient_notification.document
        
        context = {
            'patient_name': patient.get_full_name(),
            'patient_first_name': patient.first_name,
            'patient_phone': patient.phone,
            'patient_email': patient.email,
            'document_type': patient_notification.template.get_document_type_display(),
            'document_url': patient_notification.document_url,
            'hospital_name': getattr(settings, 'HOSPITAL_NAME', 'Hospital Management System'),
            'date': timezone.now().strftime('%Y-%m-%d'),
            'time': timezone.now().strftime('%H:%M'),
        }
        
        # Add document-specific context
        if hasattr(document, 'invoice_number'):
            context['invoice_number'] = document.invoice_number
        if hasattr(document, 'appointment_date'):
            context['appointment_date'] = document.appointment_date
        if hasattr(document, 'doctor'):
            context['doctor_name'] = document.doctor.get_full_name() if document.doctor else 'N/A'
        
        return context


class EmailNotificationService(NotificationService):
    """Service for sending email notifications"""
    
    def send_notification(self, patient_notification: PatientNotification) -> bool:
        """Send email notification"""
        if not self.settings or not self.settings.email_enabled:
            logger.info("Email notifications are disabled")
            return False
        
        if not patient_notification.recipient_email:
            logger.error(f"No email address for patient {patient_notification.patient.id}")
            return False
        
        try:
            context = self.get_document_context(patient_notification)
            
            # Render subject and body
            subject = self.render_template(patient_notification.subject, context)
            body = self.render_template(patient_notification.message_body, context)
            
            # Create email
            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=self.settings.email_from_address or settings.DEFAULT_FROM_EMAIL,
                to=[patient_notification.recipient_email],
            )
            
            # Add attachment if exists
            if patient_notification.attachment_path and os.path.exists(patient_notification.attachment_path):
                email.attach_file(patient_notification.attachment_path)
            
            # Send email
            result = email.send()
            
            if result:
                patient_notification.status = 'SENT'
                patient_notification.sent_at = timezone.now()
                patient_notification.save()
                
                self._log_delivery_attempt(patient_notification, 1, True, "Email sent successfully")
                return True
            else:
                self._log_delivery_attempt(patient_notification, 1, False, "Failed to send email")
                return False
                
        except Exception as e:
            error_msg = f"Email sending failed: {str(e)}"
            logger.error(error_msg)
            self._log_delivery_attempt(patient_notification, 1, False, error_msg)
            return False
    
    def _log_delivery_attempt(self, notification: PatientNotification, attempt: int, success: bool, message: str):
        """Log delivery attempt"""
        DeliveryLog.objects.create(
            notification=notification,
            attempt_number=attempt,
            success=success,
            error_message=message if not success else "",
        )


class WhatsAppNotificationService(NotificationService):
    """Service for sending WhatsApp notifications"""
    
    def send_notification(self, patient_notification: PatientNotification) -> bool:
        """Send WhatsApp notification"""
        if not self.settings or not self.settings.whatsapp_enabled:
            logger.info("WhatsApp notifications are disabled")
            return False
        
        if not patient_notification.recipient_whatsapp:
            logger.error(f"No WhatsApp number for patient {patient_notification.patient.id}")
            return False
        
        try:
            context = self.get_document_context(patient_notification)
            message = self.render_template(patient_notification.message_body, context)
            
            # Prepare WhatsApp API request
            payload = {
                "phone": patient_notification.recipient_whatsapp,
                "message": message,
                "apikey": self.settings.whatsapp_api_key,
            }
            
            # Add document link if available
            if patient_notification.document_url:
                payload["message"] += f"\n\nDocument Link: {patient_notification.document_url}"
            
            response = requests.post(
                self.settings.whatsapp_api_url,
                json=payload,
                timeout=30
            )
            
            self._log_delivery_attempt(
                patient_notification,
                1,
                response.status_code == 200,
                f"WhatsApp API response: {response.status_code}",
                api_endpoint=self.settings.whatsapp_api_url,
                request_payload=json.dumps(payload, indent=2),
                response_body=response.text,
                response_status_code=response.status_code
            )
            
            if response.status_code == 200:
                patient_notification.status = 'SENT'
                patient_notification.sent_at = timezone.now()
                patient_notification.delivery_provider = 'WhatsApp API'
                
                # Try to extract message ID from response
                try:
                    response_data = response.json()
                    if 'message_id' in response_data:
                        patient_notification.external_message_id = response_data['message_id']
                except:
                    pass
                
                patient_notification.save()
                return True
            else:
                patient_notification.status = 'FAILED'
                patient_notification.failed_at = timezone.now()
                patient_notification.error_message = f"WhatsApp API error: {response.status_code}"
                patient_notification.save()
                return False
                
        except Exception as e:
            error_msg = f"WhatsApp sending failed: {str(e)}"
            logger.error(error_msg)
            patient_notification.status = 'FAILED'
            patient_notification.failed_at = timezone.now()
            patient_notification.error_message = error_msg
            patient_notification.save()
            self._log_delivery_attempt(patient_notification, 1, False, error_msg)
            return False
    
    def _log_delivery_attempt(self, notification: PatientNotification, attempt: int, success: bool, 
                            message: str, **kwargs):
        """Log WhatsApp delivery attempt"""
        DeliveryLog.objects.create(
            notification=notification,
            attempt_number=attempt,
            success=success,
            error_message=message if not success else "",
            api_endpoint=kwargs.get('api_endpoint', ''),
            request_payload=kwargs.get('request_payload', ''),
            response_body=kwargs.get('response_body', ''),
            response_status_code=kwargs.get('response_status_code'),
        )


class TelegramNotificationService(NotificationService):
    """Service for sending Telegram notifications"""
    
    def send_notification(self, patient_notification: PatientNotification) -> bool:
        """Send Telegram notification"""
        if not self.settings or not self.settings.telegram_enabled:
            logger.info("Telegram notifications are disabled")
            return False
        
        if not patient_notification.recipient_telegram:
            logger.error(f"No Telegram chat ID for patient {patient_notification.patient.id}")
            return False
        
        try:
            context = self.get_document_context(patient_notification)
            message = self.render_template(patient_notification.message_body, context)
            
            # Telegram Bot API URL
            api_url = f"https://api.telegram.org/bot{self.settings.telegram_bot_token}/sendMessage"
            
            payload = {
                "chat_id": patient_notification.recipient_telegram,
                "text": message,
                "parse_mode": "HTML"
            }
            
            response = requests.post(api_url, json=payload, timeout=30)
            
            self._log_delivery_attempt(
                patient_notification,
                1,
                response.status_code == 200,
                f"Telegram API response: {response.status_code}",
                api_endpoint=api_url,
                request_payload=json.dumps(payload, indent=2),
                response_body=response.text,
                response_status_code=response.status_code
            )
            
            if response.status_code == 200:
                patient_notification.status = 'SENT'
                patient_notification.sent_at = timezone.now()
                patient_notification.delivery_provider = 'Telegram Bot API'
                
                # Extract message ID
                try:
                    response_data = response.json()
                    if response_data.get('ok') and 'result' in response_data:
                        patient_notification.external_message_id = str(response_data['result']['message_id'])
                except:
                    pass
                
                patient_notification.save()
                return True
            else:
                patient_notification.status = 'FAILED'
                patient_notification.failed_at = timezone.now()
                patient_notification.error_message = f"Telegram API error: {response.status_code}"
                patient_notification.save()
                return False
                
        except Exception as e:
            error_msg = f"Telegram sending failed: {str(e)}"
            logger.error(error_msg)
            patient_notification.status = 'FAILED'
            patient_notification.failed_at = timezone.now()
            patient_notification.error_message = error_msg
            patient_notification.save()
            self._log_delivery_attempt(patient_notification, 1, False, error_msg)
            return False
    
    def _log_delivery_attempt(self, notification: PatientNotification, attempt: int, success: bool, 
                            message: str, **kwargs):
        """Log Telegram delivery attempt"""
        DeliveryLog.objects.create(
            notification=notification,
            attempt_number=attempt,
            success=success,
            error_message=message if not success else "",
            api_endpoint=kwargs.get('api_endpoint', ''),
            request_payload=kwargs.get('request_payload', ''),
            response_body=kwargs.get('response_body', ''),
            response_status_code=kwargs.get('response_status_code'),
        )


class DocumentNotificationManager:
    """Main manager for sending document notifications"""
    
    def __init__(self):
        self.email_service = EmailNotificationService()
        self.whatsapp_service = WhatsAppNotificationService()
        self.telegram_service = TelegramNotificationService()
    
    def send_document_notification(self, patient, document_type: str, document_obj, document_url: str = "", attachment_path: str = ""):
        """Send notification for a document to patient via all configured channels"""
        
        # Get active templates for this document type
        templates = NotificationTemplate.objects.filter(
            document_type=document_type,
            is_active=True,
            auto_send=True
        )
        
        if not templates.exists():
            logger.info(f"No active templates found for document type: {document_type}")
            return
        
        for template in templates:
            # Create patient notification record
            patient_notification = self._create_patient_notification(
                patient, template, document_obj, document_url, attachment_path
            )
            
            if not patient_notification:
                continue
            
            # Send via appropriate channel
            success = False
            if template.channel == 'EMAIL':
                success = self.email_service.send_notification(patient_notification)
            elif template.channel == 'WHATSAPP':
                success = self.whatsapp_service.send_notification(patient_notification)
            elif template.channel == 'TELEGRAM':
                success = self.telegram_service.send_notification(patient_notification)
            
            logger.info(f"Document notification {template.channel} for {patient.get_full_name()}: {'SUCCESS' if success else 'FAILED'}")
    
    def _create_patient_notification(self, patient, template: NotificationTemplate, document_obj, document_url: str, attachment_path: str):
        """Create PatientNotification record"""
        try:
            from django.contrib.contenttypes.models import ContentType
            
            # Get content type for the document
            content_type = ContentType.objects.get_for_model(document_obj)
            
            # Get recipient details based on channel
            recipient_email = patient.email if template.channel == 'EMAIL' else ""
            recipient_phone = patient.phone if template.channel in ['SMS', 'WHATSAPP'] else ""
            recipient_whatsapp = patient.phone if template.channel == 'WHATSAPP' else ""  # Assuming same as phone
            recipient_telegram = getattr(patient, 'telegram_chat_id', '') if template.channel == 'TELEGRAM' else ""
            
            # Skip if no recipient info for this channel
            if template.channel == 'EMAIL' and not recipient_email:
                logger.warning(f"No email for patient {patient.id}, skipping email notification")
                return None
            elif template.channel == 'WHATSAPP' and not recipient_whatsapp:
                logger.warning(f"No WhatsApp for patient {patient.id}, skipping WhatsApp notification")
                return None
            elif template.channel == 'TELEGRAM' and not recipient_telegram:
                logger.warning(f"No Telegram for patient {patient.id}, skipping Telegram notification")
                return None
            
            # Create notification
            notification = PatientNotification.objects.create(
                patient=patient,
                template=template,
                content_type=content_type,
                object_id=document_obj.id,
                recipient_email=recipient_email,
                recipient_phone=recipient_phone,
                recipient_whatsapp=recipient_whatsapp,
                recipient_telegram=recipient_telegram,
                subject=template.subject_template,
                message_body=template.body_template,
                document_url=document_url,
                attachment_path=attachment_path,
                scheduled_at=timezone.now() + timezone.timedelta(minutes=template.send_delay_minutes)
            )
            
            return notification
            
        except Exception as e:
            logger.error(f"Failed to create patient notification: {str(e)}")
            return None


# Singleton instance
document_notification_manager = DocumentNotificationManager()
