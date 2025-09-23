# Custom Admin Dashboard Views
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from apps.patients.models import Patient
from apps.appointments.models import Appointment
from apps.doctors.models import Doctor

# Try to import optional models - handle if they don't exist yet
try:
    from apps.laboratory.models import LabOrder
except ImportError:
    LabOrder = None


@staff_member_required
def admin_dashboard_data(request):
    """API endpoint for admin dashboard data"""
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    last_7_days = today - timedelta(days=7)
    
    # Patient statistics
    total_patients = Patient.objects.count()
    new_patients_today = Patient.objects.filter(created_at__date=today).count()
    new_patients_week = Patient.objects.filter(created_at__date__gte=last_7_days).count()
    new_patients_month = Patient.objects.filter(created_at__date__gte=last_30_days).count()
    
    # Appointment statistics
    total_appointments = Appointment.objects.count()
    appointments_today = Appointment.objects.filter(appointment_date=today).count()
    appointments_pending = Appointment.objects.filter(status='scheduled').count()
    appointments_completed = Appointment.objects.filter(status='completed').count()
    
    # Doctor statistics
    total_doctors = Doctor.objects.count()
    active_doctors = Doctor.objects.filter(is_active=True).count()
    
    # Lab statistics - safely handle if LabOrder model doesn't exist
    if LabOrder:
        try:
            lab_orders_today = LabOrder.objects.filter(created_at__date=today).count()
            lab_orders_pending = LabOrder.objects.filter(status='pending').count()
        except Exception:
            lab_orders_today = 0
            lab_orders_pending = 0
    else:
        lab_orders_today = 0
        lab_orders_pending = 0
    
    # Financial statistics
    try:
        from apps.billing.models import Invoice
        revenue_today = Invoice.objects.filter(
            created_at__date=today,
            status='paid'
        ).aggregate(total=Sum('final_amount'))['total'] or 0
        
        revenue_month = Invoice.objects.filter(
            created_at__date__gte=last_30_days,
            status='paid'
        ).aggregate(total=Sum('final_amount'))['total'] or 0
    except:
        revenue_today = 0
        revenue_month = 0
    
    # IPD statistics
    try:
        from apps.ipd.models import IPDRecord
        ipd_patients = IPDRecord.objects.filter(status='Admitted').count()
        ipd_discharges_today = IPDRecord.objects.filter(
            discharge_date__date=today
        ).count()
    except:
        ipd_patients = 0
        ipd_discharges_today = 0
    
    # Recent activity
    recent_patients = Patient.objects.order_by('-created_at')[:5].values(
        'first_name', 'last_name', 'phone', 'created_at'
    )
    
    recent_appointments = Appointment.objects.select_related(
        'patient', 'doctor__user'
    ).order_by('-created_at')[:5].values(
        'patient__first_name', 'patient__last_name',
        'doctor__user__first_name', 'doctor__user__last_name',
        'appointment_date', 'status'
    )
    
    # Chart data - Appointments by day (last 7 days)
    appointment_chart_data = []
    for i in range(7):
        date = today - timedelta(days=i)
        count = Appointment.objects.filter(appointment_date=date).count()
        appointment_chart_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    appointment_chart_data.reverse()
    
    # Chart data - Patients by month (last 6 months)
    patient_chart_data = []
    for i in range(6):
        date = today.replace(day=1) - timedelta(days=30*i)
        count = Patient.objects.filter(
            created_at__year=date.year,
            created_at__month=date.month
        ).count()
        patient_chart_data.append({
            'month': date.strftime('%Y-%m'),
            'count': count
        })
    patient_chart_data.reverse()
    
    # Specialization-wise appointment distribution (fixed field name)
    department_data = []
    try:
        department_data = list(
            Appointment.objects.values('doctor__specialization')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )
    except Exception:
        # Handle case where relationship doesn't exist or fields are different
        department_data = []
    
    return JsonResponse({
        'stats': {
            'patients': {
                'total': total_patients,
                'today': new_patients_today,
                'week': new_patients_week,
                'month': new_patients_month
            },
            'appointments': {
                'total': total_appointments,
                'today': appointments_today,
                'pending': appointments_pending,
                'completed': appointments_completed
            },
            'doctors': {
                'total': total_doctors,
                'active': active_doctors
            },
            'laboratory': {
                'orders_today': lab_orders_today,
                'pending': lab_orders_pending
            },
            'financial': {
                'revenue_today': float(revenue_today),
                'revenue_month': float(revenue_month)
            },
            'ipd': {
                'admitted': ipd_patients,
                'discharges_today': ipd_discharges_today
            }
        },
        'recent_activity': {
            'patients': list(recent_patients),
            'appointments': list(recent_appointments)
        },
        'charts': {
            'appointments_weekly': appointment_chart_data,
            'patients_monthly': patient_chart_data,
            'departments': department_data
        }
    })


@staff_member_required  
def admin_dashboard_view(request):
    """Custom admin dashboard view"""
    context = {
        'title': 'Hospital Dashboard',
        'has_permission': True,
    }
    # Render the dashboard
    return render(request, 'admin/index.html', context)