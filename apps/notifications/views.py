# Create your views here.
from django.shortcuts import render
from django.http import JsonResponse
from django.http import HttpResponse
from django.template.loader import render_to_string
from .models import Notification

def recent_notifications(request):
    # For now, let's just return some dummy data
    notifications = [
        {"message": "New patient registered", "time": "2 hours ago"},
        {"message": "Appointment rescheduled", "time": "4 hours ago"},
        {"message": "Lab results ready", "time": "1 day ago"},
    ]
    
    html = render_to_string('notifications/recent_list.html', {'notifications': notifications})
    return HttpResponse(html)

def get_notifications(request):
    notifications = Notification.objects.filter(
        recipient=request.user,
        read=False
    )[:5]
    
    html = render_to_string(
        'notifications/notification_list.html',
        {'notifications': notifications}
    )
    
    return JsonResponse({
        'html': html,
        'count': notifications.count()
    })

def mark_as_read(request, notification_id):
    try:
        notification = Notification.objects.get(
            id=notification_id,
            recipient=request.user
        )
        notification.read = True
        notification.save()
        return JsonResponse({'status': 'success'})
    except Notification.DoesNotExist:
        return JsonResponse({'status': 'error'}, status=404)