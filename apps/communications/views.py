# Communication views and API endpoints
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction
import json
import logging

from .models import CommunicationLog, CommunicationTemplate, PatientCommunicationPreference
from apps.appointments.models import Appointment
from apps.patients.models import Patient
from django.contrib import messages
from django.shortcuts import redirect
from django.core.paginator import Paginator

logger = logging.getLogger(__name__)


@login_required
def communications_dashboard(request):
    """Communications dashboard with stats and management"""
    from django.db.models import Count, Q
    from datetime import datetime, timedelta
    
    # Get communication stats
    today = timezone.now().date()
    last_7_days = today - timedelta(days=7)
    
    stats = {
        'total_today': CommunicationLog.objects.filter(
            sent_at__date=today
        ).count(),
        'total_week': CommunicationLog.objects.filter(
            sent_at__date__gte=last_7_days
        ).count(),
        'by_channel': CommunicationLog.objects.values('channel').annotate(
            count=Count('id')
        ),
        'by_status': CommunicationLog.objects.values('status').annotate(
            count=Count('id')
        ),
        'recent_logs': CommunicationLog.objects.select_related(
            'appointment', 'patient', 'sent_by'
        ).order_by('-sent_at')[:10],
    }
    
    # Get templates count
    templates_count = CommunicationTemplate.objects.count()
    
    context = {
        'stats': stats,
        'templates_count': templates_count,
    }
    
    return render(request, 'communications/dashboard.html', context)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def track_communication(request):
    """Track communication attempts"""
    try:
        data = json.loads(request.body)
        
        appointment_id = data.get('appointment_id')
        patient_id = data.get('patient_id')
        channel = data.get('channel')
        
        if not all([appointment_id, channel]):
            return JsonResponse({'success': False, 'error': 'Missing required fields'})
        
        # Get appointment and patient
        appointment = get_object_or_404(Appointment, id=appointment_id)
        patient = appointment.patient if not patient_id else get_object_or_404(Patient, id=patient_id)
        
        # Create communication log entry
        comm_log = CommunicationLog.objects.create(
            appointment=appointment,
            patient=patient,
            sent_by=request.user,
            channel=channel,
            template_type='reminder',
            recipient_phone=patient.phone or '',
            recipient_email=patient.email or '',
            message=f"Manual {channel} communication initiated",
            status='sent',
            user_agent=data.get('user_agent', ''),
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return JsonResponse({
            'success': True, 
            'log_id': comm_log.id,
            'message': 'Communication tracked successfully'
        })
        
    except Exception as e:
        logger.error(f"Communication tracking error: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Tracking failed'})


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def bulk_communication(request):
    """Send bulk communications to multiple patients"""
    try:
        data = json.loads(request.body)
        
        appointment_ids = data.get('appointment_ids', [])
        channel = data.get('channel')
        template_type = data.get('template', 'reminder')
        
        if not appointment_ids or not channel:
            return JsonResponse({'success': False, 'error': 'Missing required fields'})
        
        # Get appointments
        appointments = Appointment.objects.filter(
            id__in=appointment_ids
        ).select_related('patient', 'doctor')
        
        if not appointments.exists():
            return JsonResponse({'success': False, 'error': 'No appointments found'})
        
        sent_count = 0
        failed_count = 0
        
        with transaction.atomic():
            for appointment in appointments:
                try:
                    # Check patient preferences
                    prefs = getattr(appointment.patient, 'communication_preferences', None)
                    if prefs and not prefs.can_receive(channel):
                        continue
                    
                    # Get template
                    template = CommunicationTemplate.objects.filter(
                        template_type=template_type,
                        channel=channel,
                        is_active=True
                    ).first()
                    
                    if template:
                        # Render message
                        context = {
                            'patient_name': appointment.patient.get_full_name(),
                            'doctor_name': appointment.doctor.get_full_name(),
                            'appointment_date': appointment.appointment_date.strftime('%B %d, %Y'),
                            'appointment_time': appointment.appointment_time.strftime('%I:%M %p'),
                            'department': appointment.department or 'General',
                        }
                        subject, message = template.render(context)
                    else:
                        message = f"Appointment reminder for {appointment.appointment_date} at {appointment.appointment_time}"
                        subject = "Appointment Reminder"
                    
                    # Create communication log
                    CommunicationLog.objects.create(
                        appointment=appointment,
                        patient=appointment.patient,
                        sent_by=request.user,
                        channel=channel,
                        template_type=template_type,
                        recipient_phone=appointment.patient.phone or '',
                        recipient_email=appointment.patient.email or '',
                        message=message,
                        subject=subject,
                        status='sent',
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        ip_address=request.META.get('REMOTE_ADDR')
                    )
                    
                    sent_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to send to {appointment.patient}: {str(e)}")
                    failed_count += 1
        
        return JsonResponse({
            'success': True,
            'sent_count': sent_count,
            'failed_count': failed_count,
            'message': f'Bulk communication sent to {sent_count} patients'
        })
        
    except Exception as e:
        logger.error(f"Bulk communication error: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Bulk communication failed'})


@login_required
def communication_history(request, appointment_id=None):
    """View communication history"""
    communications = CommunicationLog.objects.all()
    
    if appointment_id:
        appointment = get_object_or_404(Appointment, id=appointment_id)
        communications = communications.filter(appointment=appointment)
    
    communications = communications.select_related(
        'appointment', 'patient', 'sent_by'
    ).order_by('-sent_at')
    
    context = {
        'communications': communications,
        'appointment': appointment if appointment_id else None,
    }
    
    return render(request, 'communications/history.html', context)


@login_required
def template_list(request):
    """List all communication templates with management options"""
    # Check permissions
    if not request.user.has_module_permission('communications'):
        return render(request, '403.html', {'message': 'Access denied to communications module'})
    
    if request.user.role not in ['ADMIN', 'SUPERADMIN']:
        return render(request, '403.html', {'message': 'Only hospital admins can manage templates'})
    
    templates = CommunicationTemplate.objects.all().order_by('-created_at')
    
    # Filter by channel if requested
    channel_filter = request.GET.get('channel')
    if channel_filter:
        templates = templates.filter(channel=channel_filter)
    
    # Paginate
    paginator = Paginator(templates, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'templates': page_obj,
        'channel_filter': channel_filter,
        'channels': ['whatsapp', 'telegram', 'viber', 'email', 'sms'],
    }
    return render(request, 'communications/message_list.html', context)


@login_required
def template_detail(request, template_id):
    """View template details"""
    if not request.user.has_module_permission('communications'):
        return render(request, '403.html', {'message': 'Access denied to communications module'})
    
    template = get_object_or_404(CommunicationTemplate, id=template_id)
    
    # Get usage stats - CommunicationLog doesn't have template field, only template_type
    # For now, we'll show 0 usage until we implement proper template tracking
    usage_count = 0
    recent_usage = []
    
    context = {
        'template': template,
        'usage_count': usage_count,
        'recent_usage': recent_usage,
    }
    return render(request, 'communications/templates/detail.html', context)


@login_required
@csrf_protect
def template_create(request):
    """Create new communication template"""
    if not request.user.has_module_permission('communications'):
        return render(request, '403.html', {'message': 'Access denied to communications module'})
    
    if request.user.role not in ['ADMIN', 'SUPERADMIN']:
        return render(request, '403.html', {'message': 'Only hospital admins can manage templates'})
    
    if request.method == 'POST':
        name = request.POST.get('name')
        channel = request.POST.get('channel')
        template_type = request.POST.get('template_type')
        subject_template = request.POST.get('subject_template', '')
        message_template = request.POST.get('message_template')
        is_active = request.POST.get('is_active') == 'on'
        
        try:
            template = CommunicationTemplate.objects.create(
                name=name,
                channel=channel,
                template_type=template_type,
                subject_template=subject_template,
                message_template=message_template,
                is_active=is_active
            )
            messages.success(request, f'Template "{template.name}" created successfully!')
            return redirect('communications:template_detail', template_id=template.id)
        except Exception as e:
            messages.error(request, f'Error creating template: {str(e)}')
    
    context = {
        'channels': ['whatsapp', 'telegram', 'viber', 'email', 'sms'],
        'template_types': ['appointment_reminder', 'appointment_confirmation', 'appointment_cancellation', 
                          'test_result', 'payment_reminder', 'general'],
    }
    return render(request, 'communications/templates/create.html', context)


@login_required
@csrf_protect
def template_edit(request, template_id):
    """Edit communication template"""
    if not request.user.has_module_permission('communications'):
        return render(request, '403.html', {'message': 'Access denied to communications module'})
    
    if request.user.role not in ['ADMIN', 'SUPERADMIN']:
        return render(request, '403.html', {'message': 'Only hospital admins can manage templates'})
    
    template = get_object_or_404(CommunicationTemplate, id=template_id)
    
    if request.method == 'POST':
        template.name = request.POST.get('name')
        template.channel = request.POST.get('channel')
        template.template_type = request.POST.get('template_type')
        template.subject_template = request.POST.get('subject_template', '')
        template.message_template = request.POST.get('message_template')
        template.is_active = request.POST.get('is_active') == 'on'
        
        try:
            template.save()
            messages.success(request, f'Template "{template.name}" updated successfully!')
            return redirect('communications:template_detail', template_id=template.id)
        except Exception as e:
            messages.error(request, f'Error updating template: {str(e)}')
    
    context = {
        'template': template,
        'channels': ['whatsapp', 'telegram', 'viber', 'email', 'sms'],
        'template_types': ['appointment_reminder', 'appointment_confirmation', 'appointment_cancellation', 
                          'test_result', 'payment_reminder', 'general'],
    }
    return render(request, 'communications/templates/edit.html', context)


@login_required
@require_http_methods(["POST"])
def update_communication_status(request, log_id):
    """Update communication status (for webhooks)"""
    try:
        data = json.loads(request.body)
        status = data.get('status')
        
        if status not in ['delivered', 'read', 'failed']:
            return JsonResponse({'success': False, 'error': 'Invalid status'})
        
        comm_log = get_object_or_404(CommunicationLog, id=log_id)
        
        if status == 'delivered':
            comm_log.mark_delivered()
        elif status == 'read':
            comm_log.mark_read()
        elif status == 'failed':
            comm_log.mark_failed(data.get('error', ''))
        
        return JsonResponse({'success': True, 'message': 'Status updated'})
        
    except Exception as e:
        logger.error(f"Status update error: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Update failed'})
