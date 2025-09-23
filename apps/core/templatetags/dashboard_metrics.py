# ZAIN HMS - Unified System Dashboard Metrics Template Tags
from django import template
from django.db import models
from django.utils import timezone
from datetime import date, datetime, timedelta

register = template.Library()

@register.inclusion_tag('admin/partials/system_metrics.html', takes_context=True)
def system_metrics(context):
    """Generate unified system metrics for ZAIN HMS dashboard"""
    
    try:
        # Import models safely
        from apps.patients.models import Patient
        from apps.appointments.models import Appointment
        from apps.doctors.models import Doctor
        from apps.accounts.models import CustomUser
        
        today = date.today()
        
        # Basic counts
        total_patients = Patient.objects.count()
        total_appointments = Appointment.objects.count()
        total_doctors = Doctor.objects.filter(is_active=True).count()
        total_staff = CustomUser.objects.exclude(role='PATIENT').count()
        
        # Today's activity
        patients_today = Patient.objects.filter(created_at__date=today).count()
        appointments_today = Appointment.objects.filter(appointment_date=today).count()
        
        # Upcoming appointments (next 5)
        upcoming_appointments = Appointment.objects.filter(
            appointment_date__gte=today,
            status__in=['SCHEDULED', 'CONFIRMED']
        ).select_related('patient', 'doctor')[:5]
        
        # Revenue approximation (if billing exists)
        revenue_today = 0.0
        try:
            from apps.billing.models import Bill
            revenue_today = float(
                Bill.objects.filter(
                    created_at__date=today,
                    status='PAID'
                ).aggregate(total=models.Sum('total_amount'))['total'] or 0.0
            )
        except ImportError:
            pass
        
        # Doctor utilization (appointments per doctor)
        doctor_utilization = []
        try:
            utilization = Appointment.objects.filter(
                appointment_date=today
            ).values(
                'doctor__user__first_name', 
                'doctor__user__last_name'
            ).annotate(
                count=models.Count('id')
            ).order_by('-count')[:5]
            
            doctor_utilization = [
                {
                    'name': f"{u['doctor__user__first_name']} {u['doctor__user__last_name']}",
                    'appointments': u['count']
                } for u in utilization if u['doctor__user__first_name']
            ]
        except Exception:
            pass
        
        return {
            'total_patients': total_patients,
            'total_appointments': total_appointments,
            'total_doctors': total_doctors,
            'total_staff': total_staff,
            'patients_today': patients_today,
            'appointments_today': appointments_today,
            'upcoming': upcoming_appointments,
            'doctor_utilization': doctor_utilization,
            'revenue_today': revenue_today,
            'system_name': 'ZAIN HMS',
        }
        
    except Exception as e:
        # Return safe defaults if there are any errors
        return {
            'total_patients': 0,
            'total_appointments': 0,
            'total_doctors': 0,
            'total_staff': 0,
            'patients_today': 0,
            'appointments_today': 0,
            'upcoming': [],
            'doctor_utilization': [],
            'revenue_today': 0.0,
            'system_name': 'ZAIN HMS',
            'error': str(e)
        }

@register.simple_tag
def zain_hms_version():
    """Return ZAIN HMS version"""
    return "1.0.0 - Unified System"

@register.filter
def currency(value):
    """Format currency values"""
    try:
        return f"${float(value):,.2f}"
    except (ValueError, TypeError):
        return "$0.00"
