"""
Dashboard services for ZAIN HMS
Business logic and data services for dashboard functionality.
"""
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from django.core.cache import cache
from django.db import connection
from datetime import datetime, timedelta
import json
import logging

from .models import DashboardMetric, DashboardCache, ActivityLog
from apps.patients.models import Patient
from apps.appointments.models import Appointment
from apps.billing.models import Bill
from apps.accounts.models import CustomUser

logger = logging.getLogger(__name__)


class DashboardMetricsService:
    """Service for calculating and caching dashboard metrics"""
    
    @classmethod
    def get_patient_metrics(cls, user=None):
        """Get comprehensive patient metrics"""
        cache_key = "dashboard_metrics:patients"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            today = timezone.now().date()
            
            # Total patients
            total_patients = Patient.objects.filter(is_active=True).count()
            
            # New patients today
            new_today = Patient.objects.filter(
                registration_date__date=today,
                is_active=True
            ).count()
            
            # New patients this week
            week_start = today - timedelta(days=7)
            new_this_week = Patient.objects.filter(
                registration_date__date__gte=week_start,
                is_active=True
            ).count()
            
            # New patients this month
            month_start = today.replace(day=1)
            new_this_month = Patient.objects.filter(
                registration_date__date__gte=month_start,
                is_active=True
            ).count()
            
            # Active patients (had appointment in last 90 days)
            active_cutoff = today - timezone.timedelta(days=90)
            active_patients = Patient.objects.filter(
                appointments__appointment_date__gte=active_cutoff,
            ).distinct().count()
            
            data = {
                'total': total_patients,
                'new_today': new_today,
                'new_week': new_this_week,
                'new_month': new_this_month,
                'active': active_patients,
                'growth_rate': cls._calculate_growth_rate('patients', new_this_month)
            }
            
            cache.set(cache_key, data, 300)  # Cache for 5 minutes
            return data
            
        except Exception as e:
            logger.error(f"Error calculating patient metrics: {e}")
            return {
                'total': 0, 'new_today': 0, 'new_week': 0, 
                'new_month': 0, 'active': 0, 'growth_rate': 0
            }
    
    @classmethod
    def get_appointment_metrics(cls, user=None):
        """Get comprehensive appointment metrics"""
        cache_key = "dashboard_metrics:appointments"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            today = timezone.now().date()
            
            # Today's appointments
            today_total = Appointment.objects.filter(appointment_date=today).count()
            
            # Today's pending appointments
            pending_statuses = ['SCHEDULED', 'CONFIRMED', 'CHECKED_IN', 'IN_PROGRESS']
            today_pending = Appointment.objects.filter(
                appointment_date=today,
                status__in=pending_statuses
            ).count()
            
            # Today's completed appointments
            today_completed = Appointment.objects.filter(
                appointment_date=today,
                status='COMPLETED'
            ).count()
            
            # This week's appointments
            week_start = today - timedelta(days=7)
            week_total = Appointment.objects.filter(
                appointment_date__gte=week_start,
                appointment_date__lte=today
            ).count()
            
            # Upcoming appointments (next 7 days)
            week_end = today + timedelta(days=7)
            upcoming = Appointment.objects.filter(
                appointment_date__gte=today,
                appointment_date__lte=week_end,
                status__in=pending_statuses
            ).count()
            
            # Completion rate
            if today_total > 0:
                completion_rate = (today_completed / today_total) * 100
            else:
                completion_rate = 0
            
            data = {
                'today_total': today_total,
                'today_pending': today_pending,
                'today_completed': today_completed,
                'week_total': week_total,
                'upcoming': upcoming,
                'completion_rate': round(completion_rate, 1)
            }
            
            cache.set(cache_key, data, 180)  # Cache for 3 minutes
            return data
            
        except Exception as e:
            logger.error(f"Error calculating appointment metrics: {e}")
            return {
                'today_total': 0, 'today_pending': 0, 'today_completed': 0,
                'week_total': 0, 'upcoming': 0, 'completion_rate': 0
            }
    
    @classmethod
    def get_revenue_metrics(cls, user=None):
        """Get comprehensive revenue metrics"""
        cache_key = "dashboard_metrics:revenue"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            today = timezone.now().date()
            
            # Today's revenue
            today_revenue = Bill.objects.filter(
                created_at__date=today,
                status='PAID'
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            # This month's revenue
            month_start = today.replace(day=1)
            month_revenue = Bill.objects.filter(
                created_at__date__gte=month_start,
                status='PAID'
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            # Pending revenue
            pending_revenue = Bill.objects.filter(
                status__in=['PENDING', 'PARTIAL']
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            # Average bill amount
            avg_bill = Bill.objects.filter(
                status='PAID'
            ).aggregate(avg=Avg('total_amount'))['avg'] or 0
            
            # This week's revenue
            week_start = today - timedelta(days=7)
            week_revenue = Bill.objects.filter(
                created_at__date__gte=week_start,
                status='PAID'
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            data = {
                'today': float(today_revenue),
                'month': float(month_revenue),
                'week': float(week_revenue),
                'pending': float(pending_revenue),
                'average_bill': float(avg_bill),
                'growth_rate': cls._calculate_growth_rate('revenue', month_revenue)
            }
            
            cache.set(cache_key, data, 300)  # Cache for 5 minutes
            return data
            
        except Exception as e:
            logger.error(f"Error calculating revenue metrics: {e}")
            return {
                'today': 0, 'month': 0, 'week': 0,
                'pending': 0, 'average_bill': 0, 'growth_rate': 0
            }
    
    @classmethod
    def get_staff_metrics(cls, user=None):
        """Get comprehensive staff metrics"""
        cache_key = "dashboard_metrics:staff"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            # Count by role
            role_counts = CustomUser.objects.exclude(
                role='PATIENT'
            ).values('role').annotate(count=Count('id'))
            
            role_data = {}
            total_staff = 0
            
            for role_count in role_counts:
                role = role_count['role']
                count = role_count['count']
                role_data[role.lower()] = count
                total_staff += count
            
            # Active staff (logged in within last 30 days)
            active_cutoff = timezone.now() - timedelta(days=30)
            active_staff = CustomUser.objects.filter(
                last_login__gte=active_cutoff
            ).exclude(role='PATIENT').count()
            
            data = {
                'total': total_staff,
                'active': active_staff,
                'doctors': role_data.get('doctor', 0) + role_data.get('surgeon', 0),
                'nurses': role_data.get('nurse', 0),
                'admins': role_data.get('admin', 0) + role_data.get('superadmin', 0),
                'support': role_data.get('receptionist', 0) + role_data.get('technician', 0),
                'by_role': role_data
            }
            
            cache.set(cache_key, data, 600)  # Cache for 10 minutes
            return data
            
        except Exception as e:
            logger.error(f"Error calculating staff metrics: {e}")
            return {
                'total': 0, 'active': 0, 'doctors': 0, 'nurses': 0,
                'admins': 0, 'support': 0, 'by_role': {}
            }
    
    @classmethod
    def _calculate_growth_rate(cls, metric_type, current_value):
        """Calculate growth rate compared to previous period"""
        try:
            # Get previous period value (simplified calculation)
            previous_month = timezone.now().date().replace(day=1) - timedelta(days=1)
            previous_month_start = previous_month.replace(day=1)
            
            if metric_type == 'patients':
                previous_value = Patient.objects.filter(
                    registration_date__date__gte=previous_month_start,
                    registration_date__date__lte=previous_month
                ).count()
            elif metric_type == 'revenue':
                previous_value = Bill.objects.filter(
                    created_at__date__gte=previous_month_start,
                    created_at__date__lte=previous_month,
                    status='PAID'
                ).aggregate(total=Sum('total_amount'))['total'] or 0
            else:
                return 0
            
            if previous_value == 0:
                return 100 if current_value > 0 else 0
            
            growth_rate = ((current_value - previous_value) / previous_value) * 100
            return round(growth_rate, 1)
            
        except Exception:
            return 0


class DashboardChartService:
    """Service for generating chart data"""
    
    @classmethod
    def get_revenue_chart_data(cls, days=7):
        """Get revenue chart data for specified days"""
        cache_key = f"dashboard_charts:revenue:{days}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            today = timezone.now().date()
            data = []
            
            for i in range(days - 1, -1, -1):
                date = today - timedelta(days=i)
                
                daily_revenue = Bill.objects.filter(
                    created_at__date=date,
                    status='PAID'
                ).aggregate(total=Sum('total_amount'))['total'] or 0
                
                data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'label': date.strftime('%b %d'),
                    'value': float(daily_revenue)
                })
            
            cache.set(cache_key, data, 300)  # Cache for 5 minutes
            return data
            
        except Exception as e:
            logger.error(f"Error generating revenue chart data: {e}")
            return []
    
    @classmethod
    def get_appointments_chart_data(cls, days=7):
        """Get appointments chart data for specified days"""
        cache_key = f"dashboard_charts:appointments:{days}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            today = timezone.now().date()
            data = []
            
            for i in range(days - 1, -1, -1):
                date = today - timedelta(days=i)
                
                daily_count = Appointment.objects.filter(
                    appointment_date=date
                ).count()
                
                data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'label': date.strftime('%b %d'),
                    'value': daily_count
                })
            
            cache.set(cache_key, data, 300)  # Cache for 5 minutes
            return data
            
        except Exception as e:
            logger.error(f"Error generating appointments chart data: {e}")
            return []
    
    @classmethod
    def get_patient_registration_chart_data(cls, days=7):
        """Get patient registration chart data"""
        cache_key = f"dashboard_charts:patients:{days}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            today = timezone.now().date()
            data = []
            
            for i in range(days - 1, -1, -1):
                date = today - timedelta(days=i)
                
                daily_count = Patient.objects.filter(
                    registration_date=date,
                    is_active=True
                ).count()
                
                data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'label': date.strftime('%b %d'),
                    'value': daily_count
                })
            
            cache.set(cache_key, data, 300)  # Cache for 5 minutes
            return data
            
        except Exception as e:
            logger.error(f"Error generating patient chart data: {e}")
            return []


class DashboardActivityService:
    """Service for dashboard activity management"""
    
    @classmethod
    def get_recent_activities(cls, user=None, limit=10):
        """Get recent activities for dashboard"""
        cache_key = f"dashboard_activities:recent:{limit}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            activities = []
            
            # Recent patient registrations
            recent_patients = Patient.objects.filter(
                is_active=True
            ).order_by('-registration_date')[:3]
            
            for patient in recent_patients:
                # Handle timestamp conversion safely
                try:
                    if hasattr(patient, 'created_at') and patient.created_at:
                        timestamp = patient.created_at
                    elif patient.registration_date:
                        from datetime import time
                        ts = datetime.combine(patient.registration_date, time.min)
                        # If naive, make aware in current timezone
                        if ts.tzinfo is None or ts.tzinfo.utcoffset(ts) is None:
                            timestamp = timezone.make_aware(ts, timezone.get_current_timezone())
                        else:
                            timestamp = ts
                    else:
                        timestamp = timezone.now()
                except:
                    timestamp = timezone.now()
                
                # Create mock user object for template compatibility
                class MockUser:
                    def get_full_name(self):
                        return 'System'
                    @property
                    def username(self):
                        return 'system'
                
                activities.append({
                    'type': 'patient_registration',
                    'title': 'New Patient Registered',
                    'description': f'{patient.get_full_name()} has been registered',
                    'timestamp': timestamp,
                    'icon': 'person-plus',
                    'priority': 'normal',
                    'link': f'/patients/{patient.id}/',
                    'user': getattr(patient, 'registered_by', None) or getattr(patient, 'created_by', None) or user or MockUser(),
                    'user_name': 'System'  # fallback
                })
            
            # Recent appointments
            recent_appointments = Appointment.objects.filter(
                appointment_date=timezone.now().date()
            ).select_related('patient', 'doctor').order_by('-created_at')[:3]
            
            for appointment in recent_appointments:
                # Create mock user object for template compatibility
                class MockUser:
                    def get_full_name(self):
                        return 'Staff'
                    @property
                    def username(self):
                        return 'staff'
                        
                activities.append({
                    'type': 'appointment_scheduled',
                    'title': 'Appointment Scheduled',
                    'description': f'Dr. {appointment.doctor.get_full_name() if appointment.doctor else "TBD"} - {appointment.appointment_time}',
                    'timestamp': getattr(appointment, 'created_at', timezone.now()),
                    'icon': 'calendar-check',
                    'priority': 'normal',
                    'link': f'/appointments/{appointment.id}/',
                    'user': getattr(appointment, 'created_by', None) or user or MockUser(),
                    'user_name': 'Staff'  # fallback
                })
            
            # Recent payments
            recent_payments = Bill.objects.filter(
                status='PAID'
            ).select_related('patient').order_by('-updated_at')[:2]
            
            for bill in recent_payments:
                # Create mock user object for template compatibility
                class MockUser:
                    def get_full_name(self):
                        return 'Finance Team'
                    @property
                    def username(self):
                        return 'finance'
                        
                activities.append({
                    'type': 'payment_received',
                    'title': 'Payment Received',
                    'description': f'Payment of ${bill.total_amount} received from {bill.patient.get_full_name() if bill.patient else "N/A"}',
                    'timestamp': getattr(bill, 'updated_at', timezone.now()),
                    'icon': 'credit-card',
                    'priority': 'normal',
                    'link': f'/billing/{bill.id}/',
                    'user': getattr(bill, 'created_by', None) or getattr(bill, 'updated_by', None) or user or MockUser(),
                    'user_name': 'Finance'  # fallback
                })
            
            # Sort by timestamp and limit
            activities.sort(key=lambda x: x['timestamp'], reverse=True)
            activities = activities[:limit]
            
            cache.set(cache_key, activities, 180)  # Cache for 3 minutes
            return activities
            
        except Exception as e:
            logger.error(f"Error getting recent activities: {e}")
            return []
    
    @classmethod
    def get_pending_tasks(cls, user=None):
        """Get pending tasks for user role"""
        cache_key = f"dashboard_tasks:pending:{user.role if user else 'all'}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            tasks = []
            
            # Pending bills
            pending_bills = Bill.objects.filter(
                status__in=['PENDING', 'PARTIAL']
            ).count()
            
            if pending_bills > 0:
                tasks.append({
                    'type': 'pending_bills',
                    'title': 'Pending Bills',
                    'count': pending_bills,
                    'icon': 'receipt',
                    'priority': 'high',
                    'link': '/billing/?status=pending'
                })
            
            # Pending appointments
            pending_statuses = ['SCHEDULED', 'CONFIRMED', 'CHECKED_IN', 'IN_PROGRESS']
            pending_appointments = Appointment.objects.filter(
                status__in=pending_statuses,
                appointment_date=timezone.now().date()
            ).count()
            
            if pending_appointments > 0:
                tasks.append({
                    'type': 'pending_appointments',
                    'title': 'Today\'s Appointments',
                    'count': pending_appointments,
                    'icon': 'calendar-check',
                    'priority': 'normal',
                    'link': '/appointments/?date=today&status=pending'
                })
            
            # Role-specific tasks
            if user and user.role in ['ADMIN', 'SUPERADMIN']:
                # Staff pending approval (if implemented)
                tasks.append({
                    'type': 'staff_approvals',
                    'title': 'Staff Approvals',
                    'count': 2,  # Placeholder
                    'icon': 'person-check',
                    'priority': 'normal',
                    'link': '/staff/pending-approvals/'
                })
                
                # System updates
                tasks.append({
                    'type': 'system_updates',
                    'title': 'System Updates',
                    'count': 1,  # Placeholder
                    'icon': 'arrow-up-circle',
                    'priority': 'low',
                    'link': '/dashboard/settings/'
                })
            
            cache.set(cache_key, tasks, 300)  # Cache for 5 minutes
            return tasks
            
        except Exception as e:
            logger.error(f"Error getting pending tasks: {e}")
            return []


class DashboardSecurityService:
    """Service for dashboard security and monitoring"""
    
    @classmethod
    def log_dashboard_access(cls, request, dashboard_type='main'):
        """Log dashboard access for security monitoring"""
        try:
            ActivityLog.log_activity(
                user=request.user,
                action='dashboard_access',
                description=f'Accessed {dashboard_type} dashboard',
                activity_type='user_action',
                request=request,
                metadata={
                    'dashboard_type': dashboard_type,
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'referer': request.META.get('HTTP_REFERER', '')
                }
            )
        except Exception as e:
            logger.error(f"Error logging dashboard access: {e}")
    
    @classmethod
    def get_security_metrics(cls):
        """Get security-related metrics for dashboard"""
        try:
            today = timezone.now().date()
            
            # Failed login attempts today
            failed_logins = ActivityLog.objects.filter(
                activity_type='security_event',
                action='login_failed',
                timestamp__date=today
            ).count()
            
            # Successful logins today
            successful_logins = ActivityLog.objects.filter(
                activity_type='security_event',
                action='login_success',
                timestamp__date=today
            ).count()
            
            # Users active in last hour
            hour_ago = timezone.now() - timedelta(hours=1)
            active_users = ActivityLog.objects.filter(
                timestamp__gte=hour_ago,
                activity_type='user_action'
            ).values('user').distinct().count()
            
            return {
                'failed_logins': failed_logins,
                'successful_logins': successful_logins,
                'active_users': active_users,
                'security_score': cls._calculate_security_score(failed_logins, successful_logins)
            }
            
        except Exception as e:
            logger.error(f"Error getting security metrics: {e}")
            return {
                'failed_logins': 0,
                'successful_logins': 0,
                'active_users': 0,
                'security_score': 100
            }
    
    @classmethod
    def _calculate_security_score(cls, failed_logins, successful_logins):
        """Calculate a simple security score"""
        try:
            total_attempts = failed_logins + successful_logins
            if total_attempts == 0:
                return 100
            
            success_rate = (successful_logins / total_attempts) * 100
            
            # Reduce score based on failed attempts
            if failed_logins > 10:
                return max(50, success_rate - 20)
            elif failed_logins > 5:
                return max(70, success_rate - 10)
            else:
                return min(100, success_rate + 5)
                
        except Exception:
            return 100