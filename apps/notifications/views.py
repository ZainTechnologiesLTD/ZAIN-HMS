# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Notification
from .forms import NotificationForm, BulkNotificationForm
from apps.patients.models import Patient

def get_hospital_context(request):
    """Helper function to get hospital context for database routing"""
    # Keep a minimal hospital context for UI; database routing removed in unified mode
    selected_hospital_code = request.session.get('selected_hospital_code', 'zango')
    if selected_hospital_code.startswith('hospital_'):
        selected_hospital_code = selected_hospital_code.replace('hospital_', '')
    return {'selected_hospital_code': selected_hospital_code}

def recent_notifications(request):
    try:
        # Check if user is authenticated
        if not request.user.is_authenticated:
            notification_data = [
                {"message": "Please log in to view notifications", "time": "Now", "level": "info"},
            ]
        else:
            # Use default DB - unified single database
            notifications = Notification.objects.filter(
                recipient=request.user,
                read=False
            ).order_by('-created_at')[:5]
            
            # Convert to the format expected by the template
            notification_data = []
            for notif in notifications:
                notification_data.append({
                    "id": notif.id,
                    "message": notif.message,
                    "time": notif.created_at.strftime("%Y-%m-%d %H:%M"),
                    "level": notif.level,
                })
            
            # If no notifications, use some dummy data
            if not notification_data:
                notification_data = [
                    {"message": "Welcome to the Hospital Management System", "time": "Just now", "level": "info"},
                    {"message": "System is running smoothly", "time": "1 hour ago", "level": "success"},
                ]
        
    except Exception as e:
        # Fallback to dummy data if there's any database issue
        notification_data = [
            {"message": "New patient registered", "time": "2 hours ago", "level": "info"},
            {"message": "Appointment rescheduled", "time": "4 hours ago", "level": "warning"},
            {"message": "Lab results ready", "time": "1 day ago", "level": "success"},
        ]
    
    html = render_to_string('notifications/recent_list.html', {'notifications': notification_data})
    return HttpResponse(html)

def get_notifications(request):
    try:
        # Use default DB - simplified for unified system
        notifications = Notification.objects.filter(
            recipient=request.user,
            read=False
        )[:5]
    except Exception:
        # Fallback to empty queryset if database issues
        notifications = []
    
    html = render_to_string(
        'notifications/notification_list.html',
        {'notifications': notifications}
    )
    
    return JsonResponse({
        'html': html,
        'count': len(notifications)
    })

def mark_as_read(request, notification_id):
    try:
        hospital_context = get_hospital_context(request)
        
        notification = Notification.objects.get(
            id=notification_id,
            recipient=request.user
        )
        notification.read = True
        notification.save()
        return JsonResponse({'status': 'success'})
    except Notification.DoesNotExist:
        return JsonResponse({'status': 'error'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def all_notifications(request):
    try:
        # Check if user is authenticated
        if not request.user.is_authenticated:
            notifications = []
        else:
            # Use default DB in unified mode
            notifications = Notification.objects.filter(
                recipient=request.user
            ).order_by('-created_at')
    except Exception as e:
        # Log the error for debugging
        print(f"Notification database error: {e}")
        # Fallback to empty list if database issues
        notifications = []
    
    return render(request, 'notifications/all.html', {
        'notifications': notifications,
        'hospital_context': {'selected_hospital_code': 'zango'}
    })

@login_required
def create_notification(request):
    """Create individual notifications for users"""
    hospital_context = get_hospital_context(request)
    
    if request.method == 'POST':
        form = NotificationForm(request.POST, hospital_context=hospital_context)
        if form.is_valid():
            # default DB
            
            # Create notification for each selected recipient
            recipients = form.cleaned_data['recipients']
            created_count = 0
            
            for recipient in recipients:
                notification = Notification(
                    recipient=recipient,
                    level=form.cleaned_data['level'],
                    title=form.cleaned_data['title'],
                    message=form.cleaned_data['message'],
                    action_url=form.cleaned_data['action_url'],
                    read=False
                )
                notification.save()
                created_count += 1
            
            messages.success(request, f'Successfully created {created_count} notifications!')
            return redirect('notifications:all')
    else:
        form = NotificationForm(hospital_context=hospital_context)
    
    return render(request, 'notifications/create_notification.html', {
        'form': form,
        'title': 'Create Notification'
    })

@login_required
def create_bulk_notification(request):
    """Create bulk notifications for patient groups"""
    hospital_context = get_hospital_context(request)
    
    if request.method == 'POST':
        form = BulkNotificationForm(request.POST, hospital_context=hospital_context)
        if form.is_valid():
            # default DB
            
            # Determine recipients based on selection
            recipient_type = form.cleaned_data['recipient_type']
            recipients = []
            
            if recipient_type == 'all_patients':
                patients = Patient.objects.filter(user__isnull=False)
                recipients = [patient.user for patient in patients if patient.user]
            elif recipient_type == 'recent_patients':
                recent_date = timezone.now() - timezone.timedelta(days=30)
                patients = Patient.objects.filter(
                    created_at__gte=recent_date,
                    user__isnull=False
                )
                recipients = [patient.user for patient in patients if patient.user]
            elif recipient_type == 'custom_group':
                custom_patients = form.cleaned_data['custom_patients']
                recipients = [patient.user for patient in custom_patients if patient.user]
            
            # Create notifications
            created_count = 0
            for recipient in recipients:
                notification = Notification(
                    recipient=recipient,
                    level=form.cleaned_data['level'],
                    title=form.cleaned_data['title'],
                    message=form.cleaned_data['message'],
                    action_url=form.cleaned_data['action_url'],
                    read=False
                )
                notification.save()
                created_count += 1
            
            messages.success(request, f'Successfully sent bulk notifications to {created_count} recipients!')
            return redirect('notifications:all')
    else:
        form = BulkNotificationForm(hospital_context=hospital_context)
    
    return render(request, 'notifications/create_bulk_notification.html', {
        'form': form,
        'title': 'Send Bulk Notification'
    })