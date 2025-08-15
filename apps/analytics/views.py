from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Avg, Q
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from apps.patients.models import Patient
from apps.appointments.models import Appointment
from apps.billing.models import Bill
from apps.doctors.models import Doctor
from apps.emergency.models import EmergencyCase
from apps.pharmacy.models import Medicine
from django.core.paginator import Paginator

@login_required
def analytics_dashboard(request):
    """Main analytics dashboard"""
    hospital = request.user.hospital
    
    # Date range filters
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Basic statistics
    total_patients = Patient.objects.filter(hospital=hospital).count()
    total_doctors = Doctor.objects.filter(hospital=hospital).count()
    active_appointments = Appointment.objects.filter(
        hospital=hospital, 
        appointment_date=today,
        status__in=['scheduled', 'confirmed']
    ).count()
    
    # Revenue statistics
    monthly_revenue = Bill.objects.filter(
        hospital=hospital,
        created_at__date__gte=month_ago,
        status='paid'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Weekly patient registration
    weekly_patients = Patient.objects.filter(
        hospital=hospital,
        created_at__date__gte=week_ago
    ).count()
    
    # Emergency cases this month
    emergency_cases = EmergencyCase.objects.filter(
        hospital=hospital,
        created_at__date__gte=month_ago
    ).count()
    
    # Department wise patient distribution
    department_stats = Patient.objects.filter(hospital=hospital).values(
        'department__name'
    ).annotate(count=Count('id')).order_by('-count')[:5]
    
    # Monthly appointment trends
    appointment_trends = []
    for i in range(6):
        month_start = today.replace(day=1) - timedelta(days=30*i)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        count = Appointment.objects.filter(
            hospital=hospital,
            appointment_date__range=[month_start, month_end]
        ).count()
        
        appointment_trends.append({
            'month': month_start.strftime('%b %Y'),
            'count': count
        })
    
    appointment_trends.reverse()
    
    context = {
        'total_patients': total_patients,
        'total_doctors': total_doctors,
        'active_appointments': active_appointments,
        'monthly_revenue': monthly_revenue,
        'weekly_patients': weekly_patients,
        'emergency_cases': emergency_cases,
        'department_stats': department_stats,
        'appointment_trends': appointment_trends,
    }
    
    return render(request, 'analytics/dashboard.html', context)

@login_required
def patient_analytics(request):
    """Patient analytics page"""
    hospital = request.user.hospital
    
    # Age group distribution
    age_groups = {
        '0-18': Patient.objects.filter(hospital=hospital, age__lte=18).count(),
        '19-35': Patient.objects.filter(hospital=hospital, age__range=[19, 35]).count(),
        '36-50': Patient.objects.filter(hospital=hospital, age__range=[36, 50]).count(),
        '51-65': Patient.objects.filter(hospital=hospital, age__range=[51, 65]).count(),
        '65+': Patient.objects.filter(hospital=hospital, age__gte=65).count(),
    }
    
    # Gender distribution
    gender_stats = Patient.objects.filter(hospital=hospital).values('gender').annotate(
        count=Count('id')
    )
    
    # Monthly registration trends
    monthly_registrations = []
    today = timezone.now().date()
    
    for i in range(12):
        month_start = today.replace(day=1) - timedelta(days=30*i)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        count = Patient.objects.filter(
            hospital=hospital,
            created_at__date__range=[month_start, month_end]
        ).count()
        
        monthly_registrations.append({
            'month': month_start.strftime('%b %Y'),
            'count': count
        })
    
    monthly_registrations.reverse()
    
    context = {
        'age_groups': age_groups,
        'gender_stats': gender_stats,
        'monthly_registrations': monthly_registrations,
    }
    
    return render(request, 'analytics/patient_analytics.html', context)

@login_required
def financial_analytics(request):
    """Financial analytics page"""
    hospital = request.user.hospital
    today = timezone.now().date()
    
    # Revenue by month
    monthly_revenue = []
    for i in range(12):
        month_start = today.replace(day=1) - timedelta(days=30*i)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        revenue = Bill.objects.filter(
            hospital=hospital,
            created_at__date__range=[month_start, month_end],
            status='paid'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        monthly_revenue.append({
            'month': month_start.strftime('%b %Y'),
            'revenue': float(revenue)
        })
    
    monthly_revenue.reverse()
    
    # Payment method distribution
    payment_methods = Bill.objects.filter(
        hospital=hospital,
        status='paid'
    ).values('payment_method').annotate(
        count=Count('id'),
        total=Sum('total_amount')
    )
    
    # Outstanding bills
    outstanding_bills = Bill.objects.filter(
        hospital=hospital,
        status='pending'
    ).aggregate(
        count=Count('id'),
        total=Sum('total_amount')
    )
    
    context = {
        'monthly_revenue': monthly_revenue,
        'payment_methods': payment_methods,
        'outstanding_bills': outstanding_bills,
    }
    
    return render(request, 'analytics/financial_analytics.html', context)

@login_required
def api_chart_data(request):
    """API endpoint for chart data"""
    chart_type = request.GET.get('type')
    hospital = request.user.hospital
    
    if chart_type == 'appointments':
        # Last 7 days appointment data
        data = []
        today = timezone.now().date()
        
        for i in range(7):
            date = today - timedelta(days=i)
            count = Appointment.objects.filter(
                hospital=hospital,
                appointment_date=date
            ).count()
            
            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'count': count
            })
        
        return JsonResponse({'data': list(reversed(data))})
    
    elif chart_type == 'revenue':
        # Last 30 days revenue data
        data = []
        today = timezone.now().date()
        
        for i in range(30):
            date = today - timedelta(days=i)
            revenue = Bill.objects.filter(
                hospital=hospital,
                created_at__date=date,
                status='paid'
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'revenue': float(revenue)
            })
        
        return JsonResponse({'data': list(reversed(data))})
    
    return JsonResponse({'error': 'Invalid chart type'})