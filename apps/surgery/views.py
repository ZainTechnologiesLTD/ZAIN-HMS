from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta


@login_required
def surgery_list_view(request):
    """
    Display surgery management dashboard with statistics and schedules.
    """
    # Get current date/time for context
    now = timezone.now()
    today = now.date()
    
    # Mock data for demonstration (replace with actual database queries)
    context = {
        'today_date': today,
        'current_time': now,
        'stats': {
            'scheduled': 12,
            'ongoing': 3,
            'completed': 45,
            'cancelled': 2
        },
        'team_status': {
            'surgeons_available': 8,
            'nurses_on_duty': 12,
            'total_surgeons': 10,
            'total_nurses': 15
        },
        'or_status': {
            'in_use': 2,
            'available': 3,
            'maintenance': 1,
            'total_rooms': 6
        },
        'todays_surgeries': [
            {
                'time': '08:00 AM - 10:30 AM',
                'procedure': 'Appendectomy',
                'patient': 'John Smith',
                'room': 'OR-1',
                'status': 'scheduled'
            },
            {
                'time': '11:00 AM - 02:00 PM',
                'procedure': 'Cardiac Bypass Surgery',
                'patient': 'Maria Garcia',
                'room': 'OR-2',
                'status': 'ongoing'
            },
            {
                'time': '03:00 PM - 05:30 PM',
                'procedure': 'Knee Replacement',
                'patient': 'Robert Johnson',
                'room': 'OR-3',
                'status': 'scheduled'
            },
            {
                'time': '06:00 PM - 08:00 PM',
                'procedure': 'Gallbladder Removal',
                'patient': 'Lisa Wang',
                'room': 'OR-1',
                'status': 'scheduled'
            }
        ]
    }
    
    return render(request, 'surgery/surgery_list.html', context)
