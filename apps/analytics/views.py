# ZAIN HMS - Analytics Views (Optimized with Caching)
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from datetime import datetime, timedelta, date
from apps.patients.models import Patient
from apps.appointments.models import Appointment
from apps.billing.models import Bill
from apps.core.performance import CacheManager, PerformanceMonitor
import logging

logger = logging.getLogger('zain_hms.analytics')

@login_required
@PerformanceMonitor.log_slow_queries
@CacheManager.cache_result('analytics', ['dashboard', 'user'], 300)
def analytics_dashboard(request):
    """Analytics dashboard - ZAIN HMS unified system with performance optimization"""
    today = timezone.now().date()
    month_ago = today - timedelta(days=30)
    
    try:
        # Optimized queries with select_related and annotations
        
        # Patient statistics with single query
        patient_stats = Patient.objects.aggregate(
            total=Count('id'),
            new_this_month=Count('id', filter=Q(created_at__date__gte=month_ago))
        )
        
        # Appointment statistics with optimized query
        appointment_stats = Appointment.objects.aggregate(
            total=Count('id'),
            today=Count('id', filter=Q(appointment_date=today)),
            this_month=Count('id', filter=Q(appointment_date__gte=month_ago))
        )
        
        # Revenue statistics with optimized aggregation
        revenue_stats = Bill.objects.filter(status='PAID').aggregate(
            total=Sum('total_amount'),
            monthly=Sum('total_amount', filter=Q(created_at__date__gte=month_ago))
        )
        
        # Emergency cases (optimized)
        emergency_cases = 0  # Implement when emergency module is ready
        
        # Department stats with caching
        department_stats = cache.get('analytics:department_stats')
        if department_stats is None:
            department_stats = _get_department_statistics()
            cache.set('analytics:department_stats', department_stats, 900)  # 15 min
        
        # Monthly appointment trends (cached)
        appointment_trends = cache.get('analytics:appointment_trends')
        if appointment_trends is None:
            appointment_trends = _get_appointment_trends()
            cache.set('analytics:appointment_trends', appointment_trends, 1800)  # 30 min
            month_start = today.replace(day=1) - timedelta(days=30*i)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            count = Appointment.objects.filter(
                appointment_date__range=[month_start, month_end]
            ).count()
            
            appointment_trends.append({
                'month': month_start.strftime('%b %Y'),
                'appointments': count
            })
        
        appointment_trends.reverse()
        
    except Exception as e:
        # Fallback values if queries fail
        total_patients = 0
        new_patients = 0
        total_appointments = 0
        today_appointments = 0
        total_revenue = 0
        monthly_revenue = 0
        emergency_cases = 0
        department_stats = []
        appointment_trends = []
    
    context = {
        'total_patients': total_patients,
        'new_patients': new_patients,
        'total_appointments': total_appointments,
        'today_appointments': today_appointments,
        'total_revenue': total_revenue,
        'monthly_revenue': monthly_revenue,
        'emergency_cases': emergency_cases,
        'department_stats': department_stats,
        'appointment_trends': appointment_trends,
        'title': 'Analytics Dashboard - ZAIN HMS'
    }
    
    return render(request, 'analytics/dashboard.html', context)

@login_required
def patient_analytics(request):
    """Patient analytics page - ZAIN HMS unified system"""
    today = date.today()
    
    # Age group distribution
    try:
        age_groups = {
            '0-18': Patient.objects.filter(
                date_of_birth__gte=today.replace(year=today.year - 18)
            ).count(),
            '19-35': Patient.objects.filter(
                date_of_birth__gte=today.replace(year=today.year - 35),
                date_of_birth__lt=today.replace(year=today.year - 18)
            ).count(),
            '36-50': Patient.objects.filter(
                date_of_birth__gte=today.replace(year=today.year - 50),
                date_of_birth__lt=today.replace(year=today.year - 35)
            ).count(),
            '51-65': Patient.objects.filter(
                date_of_birth__gte=today.replace(year=today.year - 65),
                date_of_birth__lt=today.replace(year=today.year - 50)
            ).count(),
            '65+': Patient.objects.filter(
                date_of_birth__lt=today.replace(year=today.year - 65)
            ).count(),
        }
    except:
        age_groups = {'0-18': 0, '19-35': 0, '36-50': 0, '51-65': 0, '65+': 0}
    
    # Gender distribution
    try:
        gender_data = Patient.objects.values('gender').annotate(
            count=Count('id')
        )
    except:
        gender_data = []
    
    # Monthly registration trends
    monthly_registrations = []
    for i in range(12):
        month_start = today.replace(day=1) - timedelta(days=30*i)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        try:
            count = Patient.objects.filter(
                created_at__date__range=[month_start, month_end]
            ).count()
        except:
            count = 0
        
        monthly_registrations.append({
            'month': month_start.strftime('%b %Y'),
            'count': count
        })
    
    monthly_registrations.reverse()
    
    context = {
        'age_groups': age_groups,
        'gender_data': gender_data,
        'monthly_registrations': monthly_registrations,
        'title': 'Patient Analytics - ZAIN HMS'
    }
    
    return render(request, 'analytics/patient_analytics.html', context)

@login_required
def financial_analytics(request):
    """Financial analytics page - ZAIN HMS unified system"""
    today = timezone.now().date()
    
    try:
        # Revenue by month
        monthly_revenue = []
        for i in range(12):
            month_start = today.replace(day=1) - timedelta(days=30*i)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            revenue = Bill.objects.filter(
                status='PAID',
                created_at__date__range=[month_start, month_end]
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            monthly_revenue.append({
                'month': month_start.strftime('%b %Y'),
                'revenue': float(revenue)
            })
        
        monthly_revenue.reverse()
        
        # Payment status distribution
        payment_stats = Bill.objects.values('status').annotate(
            count=Count('id'),
            total=Sum('total_amount')
        )
        
        # Average bill amount
        avg_bill = Bill.objects.aggregate(
            avg=Avg('total_amount')
        )['avg'] or 0
        
    except Exception as e:
        monthly_revenue = []
        payment_stats = []
        avg_bill = 0
    
    context = {
        'monthly_revenue': monthly_revenue,
        'payment_stats': payment_stats,
        'avg_bill': avg_bill,
        'title': 'Financial Analytics - ZAIN HMS'
    }
    
    return render(request, 'analytics/financial_analytics.html', context)

@login_required
def api_chart_data(request):
    """API endpoint for chart data"""
    chart_type = request.GET.get('type', 'appointments')
    
    try:
        if chart_type == 'appointments':
            # Last 7 days appointment data
            data = []
            for i in range(7):
                date_check = timezone.now().date() - timedelta(days=i)
                count = Appointment.objects.filter(appointment_date=date_check).count()
                data.append({
                    'date': date_check.strftime('%Y-%m-%d'),
                    'count': count
                })
            data.reverse()
            
        elif chart_type == 'revenue':
            # Last 30 days revenue data
            data = []
            for i in range(30):
                date_check = timezone.now().date() - timedelta(days=i)
                revenue = Bill.objects.filter(
                    status='PAID',
                    created_at__date=date_check
                ).aggregate(total=Sum('total_amount'))['total'] or 0
                data.append({
                    'date': date_check.strftime('%Y-%m-%d'),
                    'revenue': float(revenue)
                })
            data.reverse()
            
        else:
            data = []
            
        return JsonResponse({
            'status': 'success',
            'data': data
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'data': []
        }, status=500)
