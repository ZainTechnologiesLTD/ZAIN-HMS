# dashboard/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from patients.models import Patient
from appointments.models import Appointment
from billing.models import Bill
from emergency.models import EmergencyCase

@login_required
def dashboard_home(request):
    """Enhanced dashboard with real-time statistics"""
    today = timezone.now().date()
    user = request.user
    
    context = {
        'today': today,
    }
    
    # Role-based dashboard data
    if user.role in ['ADMIN', 'SUPERADMIN']:
        # Admin Dashboard
        context.update({
            'total_patients': Patient.objects.filter(hospital=user.hospital).count(),
            'today_appointments': Appointment.objects.filter(
                hospital=user.hospital,
                date=today
            ).count(),
            'emergency_cases': EmergencyCase.objects.filter(
                hospital=user.hospital,
                status='ACTIVE'
            ).count(),
            'pending_bills': Bill.objects.filter(
                hospital=user.hospital,
                status='PENDING'
            ).aggregate(total=Sum('amount'))['total'] or 0,
            
            # Charts data
            'appointment_chart_data': get_appointment_chart_data(user.hospital),
            'revenue_chart_data': get_revenue_chart_data(user.hospital),
            'patient_chart_data': get_patient_chart_data(user.hospital),
            
            # Recent activities
            'recent_appointments': Appointment.objects.filter(
                hospital=user.hospital
            ).select_related('patient', 'doctor')[:5],
            'recent_patients': Patient.objects.filter(
                hospital=user.hospital
            ).order_by('-created_at')[:5],
        })
        
    elif user.role == 'DOCTOR':
        # Doctor Dashboard
        context.update({
            'my_appointments_today': Appointment.objects.filter(
                doctor=user.doctor_profile,
                date=today
            ).count(),
            'my_patients': Patient.objects.filter(
                appointments__doctor=user.doctor_profile
            ).distinct().count(),
            'upcoming_appointments': Appointment.objects.filter(
                doctor=user.doctor_profile,
                date__gte=today,
                status='SCHEDULED'
            ).select_related('patient')[:10],
        })
        
    elif user.role == 'NURSE':
        # Nurse Dashboard
        context.update({
            'assigned_patients': Patient.objects.filter(
                ward_assignments__nurse=user.nurse_profile,
                ward_assignments__status='ACTIVE'
            ).count(),
            'emergency_cases': EmergencyCase.objects.filter(
                hospital=user.hospital,
                status='ACTIVE'
            ).count(),
        })
    
    elif user.role == 'RECEPTIONIST':
        # Receptionist Dashboard
        context.update({
            'pending_appointments': Appointment.objects.filter(
                hospital=user.hospital,
                status='PENDING'
            ).count(),
            'walk_in_patients': Patient.objects.filter(
                hospital=user.hospital,
                created_at__date=today,
                appointment_type='WALK_IN'
            ).count(),
        })
    
    return render(request, 'dashboard/home.html', context)

def get_appointment_chart_data(hospital):
    """Get appointment data for the last 7 days"""
    data = []
    for i in range(6, -1, -1):
        date = timezone.now().date() - timedelta(days=i)
        count = Appointment.objects.filter(
            hospital=hospital,
            date=date
        ).count()
        data.append({
            'date': date.strftime('%b %d'),
            'count': count
        })
    return data

def get_revenue_chart_data(hospital):
    """Get revenue data for the last 7 days"""
    data = []
    for i in range(6, -1, -1):
        date = timezone.now().date() - timedelta(days=i)
        revenue = Bill.objects.filter(
            hospital=hospital,
            created_at__date=date,
            status='PAID'
        ).aggregate(total=Sum('amount'))['total'] or 0
        data.append({
            'date': date.strftime('%b %d'),
            'amount': float(revenue)
        })
    return data

def get_patient_chart_data(hospital):
    """Get patient registration data"""
    data = []
    for i in range(6, -1, -1):
        date = timezone.now().date() - timedelta(days=i)
        count = Patient.objects.filter(
            hospital=hospital,
            created_at__date=date
        ).count()
        data.append({
            'date': date.strftime('%b %d'),
            'count': count
        })
    return data