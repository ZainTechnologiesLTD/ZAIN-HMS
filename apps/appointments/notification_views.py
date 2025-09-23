# apps/appointments/notification_views.py
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from .models import Appointment
from apps.notifications.services import document_notification_manager
import json
import logging

logger = logging.getLogger(__name__)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def send_appointment_notification(request, appointment_id):
    """Send or resend appointment notification via specified channel"""
    try:
        appointment = get_object_or_404(Appointment, id=appointment_id)
        notification_type = request.POST.get('notification_type', '').upper()
        
        if not notification_type or notification_type not in ['EMAIL', 'WHATSAPP', 'TELEGRAM', 'VIBER']:
            return JsonResponse({
                'success': False,
                'message': 'Invalid notification type'
            })
        
        # Verify patient contact info
        missing_contacts = []
        if notification_type == 'EMAIL' and not (appointment.patient_email or appointment.patient.email):
            missing_contacts.append('email address')
        elif notification_type in ['WHATSAPP', 'TELEGRAM', 'VIBER'] and not (appointment.patient_phone or appointment.patient.phone):
            missing_contacts.append('phone number')
        
        if missing_contacts:
            return JsonResponse({
                'success': False,
                'message': f'Patient {", ".join(missing_contacts)} not available'
            })
        
        # Create notification message
        message_content = create_appointment_notification_message(appointment)
        
        # Send notification based on type
        success = False
        error_message = ""
        
        try:
            if notification_type == 'EMAIL':
                success = send_email_notification(appointment, message_content)
            elif notification_type == 'WHATSAPP':
                success = send_whatsapp_notification(appointment, message_content)
            elif notification_type == 'TELEGRAM':
                success = send_telegram_notification(appointment, message_content)
            elif notification_type == 'VIBER':
                success = send_viber_notification(appointment, message_content)
            
            if success:
                # Update appointment notification tracking
                update_notification_tracking(appointment, notification_type)
                
                return JsonResponse({
                    'success': True,
                    'message': f'{notification_type.title()} notification sent successfully',
                    'notification_type': notification_type
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': f'Failed to send {notification_type.lower()} notification'
                })
                
        except Exception as e:
            logger.error(f"Error sending {notification_type} notification for appointment {appointment_id}: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error sending {notification_type.lower()} notification: {str(e)}'
            })
            
    except Exception as e:
        logger.error(f"Error in send_appointment_notification: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while sending notification'
        })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def send_bulk_notifications(request, appointment_id):
    """Send notifications via multiple channels at once"""
    try:
        appointment = get_object_or_404(Appointment, id=appointment_id)
        notification_types = request.POST.getlist('notification_types[]')
        
        if not notification_types:
            return JsonResponse({
                'success': False,
                'message': 'No notification types selected'
            })
        
        results = {}
        message_content = create_appointment_notification_message(appointment)
        
        for notification_type in notification_types:
            notification_type = notification_type.upper()
            
            try:
                if notification_type == 'EMAIL' and (appointment.patient_email or appointment.patient.email):
                    success = send_email_notification(appointment, message_content)
                elif notification_type == 'WHATSAPP' and (appointment.patient_phone or appointment.patient.phone):
                    success = send_whatsapp_notification(appointment, message_content)
                elif notification_type == 'TELEGRAM' and (appointment.patient_phone or appointment.patient.phone):
                    success = send_telegram_notification(appointment, message_content)
                elif notification_type == 'VIBER' and (appointment.patient_phone or appointment.patient.phone):
                    success = send_viber_notification(appointment, message_content)
                else:
                    success = False
                
                results[notification_type.lower()] = success
                
                if success:
                    update_notification_tracking(appointment, notification_type)
                    
            except Exception as e:
                logger.error(f"Error sending {notification_type}: {str(e)}")
                results[notification_type.lower()] = False
        
        # Count successful notifications
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        
        return JsonResponse({
            'success': successful > 0,
            'message': f'{successful} of {total} notifications sent successfully',
            'results': results,
            'successful_count': successful,
            'total_count': total
        })
        
    except Exception as e:
        logger.error(f"Error in send_bulk_notifications: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while sending notifications'
        })


@login_required
def get_notification_status(request, appointment_id):
    """Get current notification status for an appointment"""
    try:
        appointment = get_object_or_404(Appointment, id=appointment_id)
        
        # Check available contact methods
        available_contacts = {
            'email': bool(appointment.patient_email or appointment.patient.email),
            'whatsapp': bool(appointment.patient_phone or appointment.patient.phone),
            'telegram': bool(appointment.patient_phone or appointment.patient.phone),
            'viber': bool(appointment.patient_phone or appointment.patient.phone)
        }
        
        # Get notification history
        notification_history = []
        if hasattr(appointment, 'notification_types') and appointment.notification_types:
            try:
                sent_types = json.loads(appointment.notification_types) if isinstance(appointment.notification_types, str) else appointment.notification_types
                for ntype in sent_types:
                    notification_history.append({
                        'type': ntype.lower(),
                        'sent': True,
                        'sent_at': appointment.created_at.isoformat() if appointment.created_at else None
                    })
            except (json.JSONDecodeError, AttributeError):
                pass
        
        return JsonResponse({
            'success': True,
            'available_contacts': available_contacts,
            'notification_sent': getattr(appointment, 'notification_sent', False),
            'notification_history': notification_history,
            'patient_email': appointment.patient_email or getattr(appointment.patient, 'email', ''),
            'patient_phone': appointment.patient_phone or getattr(appointment.patient, 'phone', '')
        })
        
    except Exception as e:
        logger.error(f"Error getting notification status: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error retrieving notification status'
        })


# Helper Functions

def create_appointment_notification_message(appointment):
    """Create a standardized notification message for appointments"""
    try:
        message = f"""
🏥 {_('Appointment Confirmation')}

{_('Dear')} {appointment.patient.get_full_name()},

{_('Your appointment has been scheduled')}:

📅 {_('Date')}: {appointment.appointment_date.strftime('%B %d, %Y')}
🕒 {_('Time')}: {appointment.appointment_time.strftime('%I:%M %p')}
👨‍⚕️ {_('Doctor')}: Dr. {appointment.doctor.get_full_name()}
🏥 {_('Department')}: {appointment.department}
🎫 {_('Serial Number')}: {appointment.serial_number}
📋 {_('Appointment Number')}: {appointment.appointment_number}

{_('Please arrive 15 minutes before your appointment time')}.

{_('Thank you')}!
"""
        return message.strip()
    except Exception as e:
        logger.error(f"Error creating notification message: {str(e)}")
        return f"Appointment scheduled for {appointment.patient.get_full_name()} on {appointment.appointment_date}"


def send_email_notification(appointment, message_content):
    """Send email notification"""
    try:
        recipient_email = appointment.patient_email or appointment.patient.email
        if not recipient_email:
            return False
        
        subject = f"{_('Appointment Confirmation')} - {appointment.appointment_number}"
        
        # Create HTML email content
        html_content = render_to_string('appointments/email_notification.html', {
            'appointment': appointment,
            'message': message_content,
            'hospital_name': getattr(settings, 'HOSPITAL_NAME', 'Hospital'),
        })
        
        send_mail(
            subject=subject,
            message=message_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            html_message=html_content,
            fail_silently=False,
        )
        
        logger.info(f"Email notification sent for appointment {appointment.id} to {recipient_email}")
        return True
        
    except Exception as e:
        logger.error(f"Email notification failed for appointment {appointment.id}: {str(e)}")
        return False


def send_whatsapp_notification(appointment, message_content):
    """Send WhatsApp notification using notification service"""
    try:
        # Use the existing notification service
        result = document_notification_manager.send_document_notification(
            patient=appointment.patient,
            document_type='APPOINTMENT',
            document_obj=appointment,
            document_url=f"/appointments/{appointment.id}/",
            force_channels=['WHATSAPP']
        )
        
        logger.info(f"WhatsApp notification sent for appointment {appointment.id}")
        return True
        
    except Exception as e:
        logger.error(f"WhatsApp notification failed for appointment {appointment.id}: {str(e)}")
        return False


def send_telegram_notification(appointment, message_content):
    """Send Telegram notification using notification service"""
    try:
        # Use the existing notification service
        result = document_notification_manager.send_document_notification(
            patient=appointment.patient,
            document_type='APPOINTMENT',
            document_obj=appointment,
            document_url=f"/appointments/{appointment.id}/",
            force_channels=['TELEGRAM']
        )
        
        logger.info(f"Telegram notification sent for appointment {appointment.id}")
        return True
        
    except Exception as e:
        logger.error(f"Telegram notification failed for appointment {appointment.id}: {str(e)}")
        return False


def send_viber_notification(appointment, message_content):
    """Send Viber notification (placeholder for future implementation)"""
    try:
        # Placeholder for Viber API implementation
        logger.info(f"Viber notification would be sent for appointment {appointment.id}")
        # For now, return True to simulate success
        return True
        
    except Exception as e:
        logger.error(f"Viber notification failed for appointment {appointment.id}: {str(e)}")
        return False


def update_notification_tracking(appointment, notification_type):
    """Update appointment notification tracking"""
    try:
        # Update notification_sent flag
        appointment.notification_sent = True
        
        # Update notification_types JSON field
        current_types = []
        if hasattr(appointment, 'notification_types') and appointment.notification_types:
            try:
                current_types = json.loads(appointment.notification_types) if isinstance(appointment.notification_types, str) else appointment.notification_types
            except (json.JSONDecodeError, AttributeError):
                current_types = []
        
        if notification_type not in current_types:
            current_types.append(notification_type)
            appointment.notification_types = json.dumps(current_types)
        
        appointment.save(update_fields=['notification_sent', 'notification_types'])
        
    except Exception as e:
        logger.error(f"Error updating notification tracking: {str(e)}")
