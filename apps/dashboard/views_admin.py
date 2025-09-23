# Enhanced Dashboard Views with Advanced Analytics
# apps/dashboard/views_enhanced.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta, datetime
import json

from apps.patients.models import Patient
from apps.appointments.models import Appointment
from apps.billing.models import Bill
from apps.emergency.models import EmergencyCase
from apps.doctors.models import Doctor
from apps.nurses.models import Nurse
from apps.accounts.models import CustomUser as User


class EnhancedDashboardView(LoginRequiredMixin, TemplateView):
    """Enhanced dashboard with real-time analytics"""
    template_name = 'dashboard/enhanced_home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        hospital = user.hospital
        
        # Time periods for analytics
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        last_month = (month_start - timedelta(days=1)).replace(day=1)
        
        # Base context
        context.update({
            'today': today,
            'current_time': timezone.now(),
            'user_role': user.role,
            'hospital_name': hospital.name if hospital else 'N/A',
        })
        
        # Role-based dashboard data
        if user.role in ['ADMIN', 'SUPERADMIN']:
            context.update(self._get_admin_dashboard_data(hospital, today, yesterday, week_start, month_start))
        elif user.role == 'DOCTOR':
            context.update(self._get_doctor_dashboard_data(user, today, week_start))
        elif user.role == 'NURSE':
            context.update(self._get_nurse_dashboard_data(user, hospital, today))
        elif user.role == 'RECEPTIONIST':
            context.update(self._get_receptionist_dashboard_data(hospital, today))
        elif user.role in ['ACCOUNTANT', 'BILLING_CLERK']:
            context.update(self._get_billing_dashboard_data(hospital, today, month_start))
            
        return context
    
    def _get_admin_dashboard_data(self, hospital, today, yesterday, week_start, month_start):
        """Get comprehensive admin dashboard data"""
        
        # Patient Analytics
.count()
.count()
.count()
.count()
        
        # Calculate growth percentages
        patient_growth = self._calculate_growth(patients_today, patients_yesterday)
        
        # Appointment Analytics
.count()
.count()
        appointments_completed = Appointment.objects.filter(
            hospital=hospital, date=today, status='COMPLETED'
        ).count()
        appointments_pending = Appointment.objects.filter(
            hospital=hospital, date=today, status__in=['SCHEDULED', 'CONFIRMED']
        ).count()
        
        # Revenue Analytics
        revenue_today = Bill.objects.filter(
            hospital=hospital, created_at__date=today, status='PAID'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        revenue_this_month = Bill.objects.filter(
            hospital=hospital, created_at__date__gte=month_start, status='PAID'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        pending_bills_amount = Bill.objects.filter(
            hospital=hospital, status='PENDING'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Staff Analytics
.count()
.count()
.count()
        
        # Emergency Cases
        emergency_active = EmergencyCase.objects.filter(
            hospital=hospital, status='ACTIVE'
        ).count()
        
        emergency_today = EmergencyCase.objects.filter(
            hospital=hospital, created_at__date=today
        ).count()
        
        # Bed Occupancy (if IPD module exists)
        try:
            from apps.ipd.models import IPDRecord
            occupied_beds = IPDRecord.objects.filter(
                hospital=hospital, status='ACTIVE'
            ).count()
            # Assuming 100 total beds - this should come from hospital configuration
            bed_occupancy_rate = (occupied_beds / 100) * 100 if occupied_beds else 0
        except:
            occupied_beds = 0
            bed_occupancy_rate = 0
        
        # Recent Activities
        recent_appointments = Appointment.objects.filter(
            hospital=hospital
        ).select_related('patient', 'doctor').order_by('-created_at')[:5]
        
        recent_patients = Patient.objects.filter(
            hospital=hospital
        ).order_by('-created_at')[:5]
        
        recent_bills = Bill.objects.filter(
            hospital=hospital
        ).select_related('patient').order_by('-created_at')[:5]
        
        # Chart data for analytics
        appointment_chart_data = self._get_appointment_chart_data(hospital)
        revenue_chart_data = self._get_revenue_chart_data(hospital)
        patient_demographics_data = self._get_patient_demographics_data(hospital)
        department_stats = self._get_department_statistics(hospital)
        
        return {
            # Overview Stats
            'total_patients': total_patients,
            'patients_today': patients_today,
            'patients_this_week': patients_this_week,
            'patient_growth': patient_growth,
            
            'total_appointments': total_appointments,
            'appointments_today': appointments_today,
            'appointments_completed': appointments_completed,
            'appointments_pending': appointments_pending,
            
            'revenue_today': revenue_today,
            'revenue_this_month': revenue_this_month,
            'pending_bills_amount': pending_bills_amount,
            
            'active_doctors': active_doctors,
            'active_nurses': active_nurses,
            'total_staff': total_staff,
            
            'emergency_active': emergency_active,
            'emergency_today': emergency_today,
            
            'occupied_beds': occupied_beds,
            'bed_occupancy_rate': bed_occupancy_rate,
            
            # Recent Activities
            'recent_appointments': recent_appointments,
            'recent_patients': recent_patients,
            'recent_bills': recent_bills,
            
            # Chart Data
            'appointment_chart_data': json.dumps(appointment_chart_data),
            'revenue_chart_data': json.dumps(revenue_chart_data),
            'patient_demographics_data': json.dumps(patient_demographics_data),
            'department_stats': json.dumps(department_stats),
        }
    
    def _get_doctor_dashboard_data(self, user, today, week_start):
        """Get doctor-specific dashboard data"""
        try:
            doctor = user.doctor_profile
        except:
            return {}
        
        # Today's schedule
        appointments_today = Appointment.objects.filter(
            doctor=doctor, date=today
        ).order_by('time')
        
        # This week's appointments
        appointments_this_week = Appointment.objects.filter(
            doctor=doctor, date__gte=week_start
        ).count()
        
        # Patient load
        my_patients = Patient.objects.filter(
            appointments__doctor=doctor
        ).distinct().count()
        
        # Upcoming appointments
        upcoming_appointments = Appointment.objects.filter(
            doctor=doctor,
            date__gte=today,
            status__in=['SCHEDULED', 'CONFIRMED']
        ).select_related('patient').order_by('date', 'time')[:10]
        
        # Recent consultations
        recent_consultations = Appointment.objects.filter(
            doctor=doctor,
            status='COMPLETED'
        ).select_related('patient').order_by('-date', '-time')[:5]
        
        return {
            'appointments_today': appointments_today,
            'appointments_today_count': appointments_today.count(),
            'appointments_this_week': appointments_this_week,
            'my_patients': my_patients,
            'upcoming_appointments': upcoming_appointments,
            'recent_consultations': recent_consultations,
        }
    
    def _get_nurse_dashboard_data(self, user, hospital, today):
        """Get nurse-specific dashboard data"""
        try:
            nurse = user.nurse_profile
        except:
            return {}
        
        # Assigned patients (if ward management exists)
        assigned_patients = 0
        
        # Emergency cases today
        emergency_cases_today = EmergencyCase.objects.filter(
            hospital=hospital,
            created_at__date=today
        ).count()
        
        # Critical patients (this would need to be defined in patient model)
        critical_patients = 0
        
        return {
            'assigned_patients': assigned_patients,
            'emergency_cases_today': emergency_cases_today,
            'critical_patients': critical_patients,
        }
    
    def _get_receptionist_dashboard_data(self, hospital, today):
        """Get receptionist-specific dashboard data"""
        # Pending appointments
        pending_appointments = Appointment.objects.filter(
            hospital=hospital,
            status='PENDING'
        ).count()
        
        # Walk-in patients today
        walk_in_patients = Patient.objects.filter(
            hospital=hospital,
            created_at__date=today
            # Add walk-in filter if available
        ).count()
        
        # Today's appointments
        todays_appointments = Appointment.objects.filter(
            hospital=hospital,
            date=today
        ).order_by('time')
        
        return {
            'pending_appointments': pending_appointments,
            'walk_in_patients': walk_in_patients,
            'todays_appointments': todays_appointments,
        }
    
    def _get_billing_dashboard_data(self, hospital, today, month_start):
        """Get billing-specific dashboard data"""
        # Pending bills
        pending_bills = Bill.objects.filter(
            hospital=hospital,
            status='PENDING'
        ).count()
        
        pending_amount = Bill.objects.filter(
            hospital=hospital,
            status='PENDING'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Today's collections
        todays_collections = Bill.objects.filter(
            hospital=hospital,
            paid_at__date=today,
            status='PAID'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Month's collections
        months_collections = Bill.objects.filter(
            hospital=hospital,
            paid_at__date__gte=month_start,
            status='PAID'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Recent payments
        recent_payments = Bill.objects.filter(
            hospital=hospital,
            status='PAID'
        ).select_related('patient').order_by('-paid_at')[:5]
        
        return {
            'pending_bills': pending_bills,
            'pending_amount': pending_amount,
            'todays_collections': todays_collections,
            'months_collections': months_collections,
            'recent_payments': recent_payments,
        }
    
    def _calculate_growth(self, current, previous):
        """Calculate growth percentage"""
        if previous == 0:
            return 100 if current > 0 else 0
        return round(((current - previous) / previous) * 100, 1)
    
    def _get_appointment_chart_data(self, hospital):
        """Get appointment chart data for the last 7 days"""
        data = []
        labels = []
        
        for i in range(7):
            date = timezone.now().date() - timedelta(days=i)
            count = Appointment.objects.filter(
                hospital=hospital,
                date=date
            ).count()
            data.insert(0, count)
            labels.insert(0, date.strftime('%a'))
        
        return {
            'labels': labels,
            'data': data
        }
    
    def _get_revenue_chart_data(self, hospital):
        """Get revenue chart data for the last 30 days"""
        data = []
        labels = []
        
        for i in range(30):
            date = timezone.now().date() - timedelta(days=i)
            revenue = Bill.objects.filter(
                hospital=hospital,
                paid_at__date=date,
                status='PAID'
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            data.insert(0, float(revenue))
            if i % 5 == 0:  # Show every 5th day
                labels.insert(0, date.strftime('%m/%d'))
            else:
                labels.insert(0, '')
        
        return {
            'labels': labels,
            'data': data
        }
    
    def _get_patient_demographics_data(self, hospital):
        """Get patient demographics for charts"""
        # Age groups
        age_groups = {
            '0-18': 0, '19-35': 0, '36-50': 0, '51-65': 0, '65+': 0
        }
        
        # This would need proper date calculation based on patient DOB
        # For now, returning sample data
        
        # Gender distribution
.values('gender').annotate(
            count=Count('id')
        )
        
        gender_chart = {
            'labels': [item['gender'] for item in gender_data],
            'data': [item['count'] for item in gender_data]
        }
        
        return {
            'age_groups': age_groups,
            'gender_chart': gender_chart
        }
    
    def _get_department_statistics(self, hospital):
        """Get department-wise statistics"""
        # This would need proper department model
        return {
            'labels': ['Cardiology', 'Neurology', 'Orthopedics', 'Pediatrics'],
            'appointments': [45, 32, 28, 55],
            'revenue': [15000, 12000, 8000, 18000]
        }


@login_required
def dashboard_api_stats(request):
    """API endpoint for real-time dashboard statistics"""
    hospital = request.user.hospital
    today = timezone.now().date()
    
    # Get current stats
    stats = {
        'patients_today': Patient.objects.filter(
            hospital=hospital, created_at__date=today
        ).count(),
        'appointments_today': Appointment.objects.filter(
            hospital=hospital, date=today
        ).count(),
        'emergency_active': EmergencyCase.objects.filter(
            hospital=hospital, status='ACTIVE'
        ).count(),
        'revenue_today': float(Bill.objects.filter(
            hospital=hospital, created_at__date=today, status='PAID'
        ).aggregate(total=Sum('total_amount'))['total'] or 0),
        'timestamp': timezone.now().isoformat(),
    }
    
    return JsonResponse(stats)


@login_required  
def dashboard_notifications(request):
    """API endpoint for dashboard notifications"""
    hospital = request.user.hospital
    user = request.user
    
    notifications = []
    
    # Emergency notifications
    emergency_count = EmergencyCase.objects.filter(
        hospital=hospital, status='ACTIVE'
    ).count()
    
    if emergency_count > 0:
        notifications.append({
            'type': 'emergency',
            'title': 'Active Emergency Cases',
            'message': f'{emergency_count} emergency case(s) require attention',
            'priority': 'high',
            'url': '/emergency/',
            'icon': 'exclamation-triangle'
        })
    
    # Pending appointments (for receptionists)
    if user.role in ['RECEPTIONIST', 'ADMIN', 'SUPERADMIN']:
        pending_appointments = Appointment.objects.filter(
            hospital=hospital, status='PENDING'
        ).count()
        
        if pending_appointments > 0:
            notifications.append({
                'type': 'appointment',
                'title': 'Pending Appointments',
                'message': f'{pending_appointments} appointment(s) need confirmation',
                'priority': 'medium',
                'url': '/appointments/',
                'icon': 'calendar-check'
            })
    
    # Overdue bills (for billing staff)
    if user.role in ['ACCOUNTANT', 'BILLING_CLERK', 'ADMIN', 'SUPERADMIN']:
        overdue_bills = Bill.objects.filter(
            hospital=hospital,
            status='PENDING',
            due_date__lt=timezone.now().date()
        ).count()
        
        if overdue_bills > 0:
            notifications.append({
                'type': 'billing',
                'title': 'Overdue Bills',
                'message': f'{overdue_bills} bill(s) are overdue',
                'priority': 'medium',
                'url': '/billing/',
                'icon': 'currency-dollar'
            })
    
    return JsonResponse({'notifications': notifications})
