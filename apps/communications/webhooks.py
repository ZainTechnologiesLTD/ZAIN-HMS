from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.views import View
import json
import logging
from .models import CommunicationLog

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class WhatsAppWebhookView(View):
    """Handle WhatsApp delivery status webhooks"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # WhatsApp Business API webhook format
            if 'entry' in data:
                for entry in data['entry']:
                    for change in entry.get('changes', []):
                        if change.get('field') == 'messages':
                            value = change.get('value', {})
                            
                            # Handle status updates
                            for status in value.get('statuses', []):
                                message_id = status.get('id')
                                status_type = status.get('status')  # sent, delivered, read, failed
                                timestamp = status.get('timestamp')
                                
                                self._update_message_status(message_id, status_type, timestamp)
            
            return JsonResponse({'status': 'success'})
            
        except Exception as e:
            logger.error(f"WhatsApp webhook error: {str(e)}")
            return HttpResponseBadRequest(f"Error: {str(e)}")
    
    def _update_message_status(self, external_id, status, timestamp=None):
        """Update communication log status"""
        try:
            comm_log = CommunicationLog.objects.get(
                external_id=external_id,
                channel='whatsapp'
            )
            
            if timestamp:
                status_time = timezone.datetime.fromtimestamp(
                    int(timestamp), tz=timezone.utc
                )
            else:
                status_time = timezone.now()
            
            if status == 'sent':
                comm_log.status = 'sent'
            elif status == 'delivered':
                comm_log.status = 'delivered'
                comm_log.delivered_at = status_time
            elif status == 'read':
                comm_log.status = 'read'
                comm_log.read_at = status_time
            elif status == 'failed':
                comm_log.status = 'failed'
                comm_log.failed_at = status_time
            
            comm_log.save()
            logger.info(f"Updated WhatsApp message {external_id} status to {status}")
            
        except CommunicationLog.DoesNotExist:
            logger.warning(f"WhatsApp message {external_id} not found in logs")
        except Exception as e:
            logger.error(f"Error updating WhatsApp status: {str(e)}")


@method_decorator(csrf_exempt, name='dispatch')
class TelegramWebhookView(View):
    """Handle Telegram Bot API webhooks"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Handle callback queries for delivery confirmation
            if 'callback_query' in data:
                callback = data['callback_query']
                message_data = callback.get('data', '')
                
                if message_data.startswith('delivered_'):
                    external_id = message_data.replace('delivered_', '')
                    self._update_message_status(external_id, 'delivered')
            
            # Handle message events
            elif 'message' in data:
                message = data['message']
                # Handle read receipts or other status updates
                pass
            
            return JsonResponse({'status': 'success'})
            
        except Exception as e:
            logger.error(f"Telegram webhook error: {str(e)}")
            return HttpResponseBadRequest(f"Error: {str(e)}")
    
    def _update_message_status(self, external_id, status):
        """Update communication log status"""
        try:
            comm_log = CommunicationLog.objects.get(
                external_id=external_id,
                channel='telegram'
            )
            
            status_time = timezone.now()
            
            if status == 'delivered':
                comm_log.status = 'delivered'
                comm_log.delivered_at = status_time
            elif status == 'read':
                comm_log.status = 'read'
                comm_log.read_at = status_time
            elif status == 'failed':
                comm_log.status = 'failed'
                comm_log.failed_at = status_time
            
            comm_log.save()
            logger.info(f"Updated Telegram message {external_id} status to {status}")
            
        except CommunicationLog.DoesNotExist:
            logger.warning(f"Telegram message {external_id} not found in logs")
        except Exception as e:
            logger.error(f"Error updating Telegram status: {str(e)}")


@csrf_exempt
@require_http_methods(["POST"])
def email_webhook(request):
    """Handle email delivery status webhooks (SendGrid, Mailgun, etc.)"""
    try:
        data = json.loads(request.body)
        
        # SendGrid webhook format
        if isinstance(data, list):
            for event in data:
                event_type = event.get('event')
                message_id = event.get('sg_message_id') or event.get('smtp-id')
                timestamp = event.get('timestamp')
                
                if message_id and event_type:
                    _update_email_status(message_id, event_type, timestamp)
        
        # Mailgun webhook format
        elif 'event-data' in data:
            event_data = data['event-data']
            event_type = event_data.get('event')
            message_id = event_data.get('message', {}).get('headers', {}).get('message-id')
            timestamp = event_data.get('timestamp')
            
            if message_id and event_type:
                _update_email_status(message_id, event_type, timestamp)
        
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        logger.error(f"Email webhook error: {str(e)}")
        return HttpResponseBadRequest(f"Error: {str(e)}")


def _update_email_status(external_id, event_type, timestamp=None):
    """Update email communication log status"""
    try:
        comm_log = CommunicationLog.objects.get(
            external_id=external_id,
            channel='email'
        )
        
        if timestamp:
            if isinstance(timestamp, str):
                # Parse timestamp string
                from django.utils.dateparse import parse_datetime
                status_time = parse_datetime(timestamp) or timezone.now()
            else:
                status_time = timezone.datetime.fromtimestamp(
                    timestamp, tz=timezone.utc
                )
        else:
            status_time = timezone.now()
        
        # Map email events to our status
        status_mapping = {
            'delivered': 'delivered',
            'open': 'read',
            'click': 'read',
            'bounce': 'failed',
            'dropped': 'failed',
            'deferred': 'sent',
            'processed': 'sent'
        }
        
        new_status = status_mapping.get(event_type)
        if new_status:
            comm_log.status = new_status
            
            if new_status == 'delivered':
                comm_log.delivered_at = status_time
            elif new_status == 'read':
                comm_log.read_at = status_time
            elif new_status == 'failed':
                comm_log.failed_at = status_time
            
            comm_log.save()
            logger.info(f"Updated email {external_id} status to {new_status}")
        
    except CommunicationLog.DoesNotExist:
        logger.warning(f"Email message {external_id} not found in logs")
    except Exception as e:
        logger.error(f"Error updating email status: {str(e)}")


@csrf_exempt
@require_http_methods(["POST"])
def sms_webhook(request):
    """Handle SMS delivery status webhooks (Twilio, etc.)"""
    try:
        # Handle form data from Twilio
        if request.content_type == 'application/x-www-form-urlencoded':
            data = request.POST
        else:
            data = json.loads(request.body)
        
        message_sid = data.get('MessageSid') or data.get('message_id')
        message_status = data.get('MessageStatus') or data.get('status')
        
        if message_sid and message_status:
            _update_sms_status(message_sid, message_status)
        
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        logger.error(f"SMS webhook error: {str(e)}")
        return HttpResponseBadRequest(f"Error: {str(e)}")


def _update_sms_status(external_id, status):
    """Update SMS communication log status"""
    try:
        comm_log = CommunicationLog.objects.get(
            external_id=external_id,
            channel='sms'
        )
        
        status_time = timezone.now()
        
        # Map Twilio status to our status
        status_mapping = {
            'queued': 'pending',
            'sent': 'sent',
            'delivered': 'delivered',
            'undelivered': 'failed',
            'failed': 'failed'
        }
        
        new_status = status_mapping.get(status, status)
        comm_log.status = new_status
        
        if new_status == 'delivered':
            comm_log.delivered_at = status_time
        elif new_status == 'failed':
            comm_log.failed_at = status_time
        
        comm_log.save()
        logger.info(f"Updated SMS {external_id} status to {new_status}")
        
    except CommunicationLog.DoesNotExist:
        logger.warning(f"SMS message {external_id} not found in logs")
    except Exception as e:
        logger.error(f"Error updating SMS status: {str(e)}")


@require_http_methods(["GET"])
def webhook_verification(request, provider):
    """Handle webhook verification challenges"""
    if provider == 'whatsapp':
        # WhatsApp webhook verification
        verify_token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        
        # Replace with your actual verification token
        VERIFY_TOKEN = 'your_whatsapp_verify_token_here'
        
        if verify_token == VERIFY_TOKEN:
            return JsonResponse({'hub.challenge': challenge})
        else:
            return HttpResponseBadRequest('Invalid verification token')
    
    elif provider == 'telegram':
        # Telegram webhook verification
        return JsonResponse({'status': 'verified'})
    
    return HttpResponseBadRequest('Unknown provider')
