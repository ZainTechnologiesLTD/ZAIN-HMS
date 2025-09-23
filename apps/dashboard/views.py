"""
Dashboard views for ZAIN HMS
Modern enterprise-grade views with proper architecture, caching, and error handling.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView, View
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Count
from django.contrib import messages
import json
import logging
from datetime import datetime, timedelta

from .models import (
    DashboardWidget, UserDashboardLayout, DashboardMetric, 
    ActivityLog, DashboardAlert, DashboardAnalytics
)
from .services import (
    DashboardMetricsService, DashboardChartService, 
    DashboardActivityService, DashboardSecurityService
)
from apps.accounts.models import CustomUser

logger = logging.getLogger(__name__)


# Utility functions
def is_admin_user(user):
    """Check if user has admin privileges"""
    return user.is_authenticated and user.role in ['ADMIN', 'SUPERADMIN']


def is_staff_user(user):
    """Check if user is staff member"""
    return user.is_authenticated and user.role not in ['PATIENT']


# Main Dashboard Views
class DashboardHomeView(LoginRequiredMixin, TemplateView):
    """Main dashboard view with role-based routing"""
    
    def get_template_names(self):
        """Return template based on user role"""
        user = self.request.user
        
        if user.role in ['ADMIN', 'SUPERADMIN']:
            return ['dashboard/admin_dashboard.html']
        elif user.role == 'DOCTOR':
            return ['dashboard/doctor_dashboard.html']
        elif user.role == 'NURSE':
            return ['dashboard/nurse_dashboard.html']
        elif user.role == 'PATIENT':
            return ['dashboard/patient_dashboard.html']
        else:
            return ['dashboard/staff_dashboard.html']
    
    def get_context_data(self, **kwargs):
        """Get context data for dashboard"""
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Log dashboard access
        DashboardSecurityService.log_dashboard_access(self.request)
        
        # Track page view analytics
        DashboardAnalytics.track_page_view(user, 'dashboard')
        
        # Common context
        context.update({
            'today': timezone.now().date(),
            'now': timezone.now(),
            'user': user,
            'user_layout': self._get_user_layout(user),
            'alerts': self._get_user_alerts(user),
        })
        
        # Role-specific context
        if user.role in ['ADMIN', 'SUPERADMIN']:
            context.update(self._get_admin_context(user))
        elif user.role == 'DOCTOR':
            context.update(self._get_doctor_context(user))
        elif user.role == 'NURSE':
            context.update(self._get_nurse_context(user))
        elif user.role == 'PATIENT':
            context.update(self._get_patient_context(user))
        else:
            context.update(self._get_staff_context(user))
        
        return context
    
    def _get_user_layout(self, user):
        """Get user dashboard layout preferences"""
        try:
            return UserDashboardLayout.objects.get(user=user)
        except UserDashboardLayout.DoesNotExist:
            # Create default layout for new users
            return UserDashboardLayout.objects.create(
                user=user,
                layout_config={'grid': 'default'},
                widget_settings={}
            )
    
    def _get_user_alerts(self, user):
        """Get alerts visible to user"""
        try:
            # Simple approach for SQLite compatibility
            all_alerts = DashboardAlert.objects.filter(is_active=True)
            user_alerts = []
            
            for alert in all_alerts:
                # Check if user should see this alert
                if (alert.target_users.filter(id=user.id).exists() or 
                    not alert.target_users.exists() or
                    (hasattr(alert, 'target_roles') and not alert.target_roles)):
                    user_alerts.append(alert)
                    if len(user_alerts) >= 5:
                        break
            
            return user_alerts
        except Exception as e:
            logger.error(f"Error getting user alerts: {e}")
            return []
    
    def _get_admin_context(self, user):
        """Get admin dashboard context"""
        try:
            # Get comprehensive metrics
            patient_metrics = DashboardMetricsService.get_patient_metrics(user)
            appointment_metrics = DashboardMetricsService.get_appointment_metrics(user)
            revenue_metrics = DashboardMetricsService.get_revenue_metrics(user)
            staff_metrics = DashboardMetricsService.get_staff_metrics(user)
            
            # Get chart data and serialize to JSON for JavaScript consumption
            revenue_chart = DashboardChartService.get_revenue_chart_data(7)
            appointments_chart = DashboardChartService.get_appointments_chart_data(7)
            patients_chart = DashboardChartService.get_patient_registration_chart_data(7)
            
            # Get activities and tasks
            recent_activities = DashboardActivityService.get_recent_activities(user, 10)
            pending_tasks = DashboardActivityService.get_pending_tasks(user)
            
            # Get security metrics
            security_metrics = DashboardSecurityService.get_security_metrics()
            
            return {
                # Metrics
                'patient_metrics': patient_metrics,
                'appointment_metrics': appointment_metrics,
                'revenue_metrics': revenue_metrics,
                'staff_metrics': staff_metrics,
                'security_metrics': security_metrics,
                
                # Chart data (both raw and JSON-serialized for JavaScript)
                'revenue_chart_data': revenue_chart,
                'revenue_chart_json': json.dumps(revenue_chart),
                'appointments_chart_data': appointments_chart,
                'appointments_chart_json': json.dumps(appointments_chart),
                'patients_chart_data': patients_chart,
                
                # Activities and tasks
                'recent_activities': recent_activities,
                'pending_tasks': pending_tasks,
                
                # Quick stats for backward compatibility
                'total_patients': patient_metrics['total'],
                'new_patients_today': patient_metrics['new_today'],
                'total_doctors': staff_metrics['doctors'],
                'total_nurses': staff_metrics['nurses'],
                'today_appointments': appointment_metrics['today_total'],
                'pending_appointments': appointment_metrics['today_pending'],
                'revenue_today': revenue_metrics['today'],
                'revenue_month': revenue_metrics['month'],
                'total_staff': staff_metrics['total'],
                
                # Template flags
                'is_admin': True,
                'dashboard_type': 'admin'
            }
            
        except Exception as e:
            logger.error(f"Error getting admin dashboard context: {e}")
            return self._get_fallback_admin_context()
    
    def _get_fallback_admin_context(self):
        """Fallback context for admin dashboard"""
        return {
            'patient_metrics': {'total': 0, 'new_today': 0, 'growth_rate': 0},
            'appointment_metrics': {'today_total': 0, 'today_pending': 0, 'completion_rate': 0},
            'revenue_metrics': {'today': 0, 'month': 0, 'growth_rate': 0},
            'staff_metrics': {'total': 0, 'doctors': 0, 'nurses': 0},
            'security_metrics': {'security_score': 100},
            'revenue_chart_data': [],
            'revenue_chart_json': '[]',
            'appointments_chart_data': [],
            'appointments_chart_json': '[]',
            'patients_chart_data': [],
            'recent_activities': [],
            'pending_tasks': [],
            'total_patients': 0,
            'new_patients_today': 0,
            'total_doctors': 0,
            'total_nurses': 0,
            'today_appointments': 0,
            'pending_appointments': 0,
            'revenue_today': 0,
            'revenue_month': 0,
            'total_staff': 0,
            'is_admin': True,
            'dashboard_type': 'admin'
        }
    
    def _get_doctor_context(self, user):
        """Get doctor dashboard context"""
        try:
            from apps.doctors.models import Doctor
            from apps.appointments.models import Appointment
            
            doctor = Doctor.objects.get(user=user)
            today = timezone.now().date()
            
            # Doctor's appointments
            my_appointments_today = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=today
            ).count()
            
            my_patients = Appointment.objects.filter(
                doctor=doctor
            ).values('patient').distinct().count()
            
            my_pending_appointments = Appointment.objects.filter(
                doctor=doctor,
                status='SCHEDULED'
            ).count()
            
            upcoming_appointments = Appointment.objects.filter(
                doctor=doctor,
                appointment_date__gte=today,
                status='SCHEDULED'
            ).select_related('patient').order_by('appointment_date', 'appointment_time')[:5]
            
            return {
                'my_appointments_today': my_appointments_today,
                'my_patients': my_patients,
                'my_pending_appointments': my_pending_appointments,
                'upcoming_appointments': upcoming_appointments,
                'doctor_profile': doctor,
                'dashboard_type': 'doctor'
            }
            
        except Exception as e:
            logger.error(f"Error getting doctor dashboard context: {e}")
            return {
                'my_appointments_today': 0,
                'my_patients': 0,
                'my_pending_appointments': 0,
                'upcoming_appointments': [],
                'doctor_profile': None,
                'dashboard_type': 'doctor'
            }
    
    def _get_nurse_context(self, user):
        """Get nurse dashboard context"""
        try:
            # Nurse-specific metrics would go here
            return {
                'assigned_patients': 0,  # Placeholder
                'completed_tasks': 0,    # Placeholder
                'pending_tasks': 0,      # Placeholder
                'dashboard_type': 'nurse'
            }
        except Exception as e:
            logger.error(f"Error getting nurse dashboard context: {e}")
            return {'dashboard_type': 'nurse'}
    
    def _get_patient_context(self, user):
        """Get patient dashboard context"""
        try:
            from apps.appointments.models import Appointment
            from apps.billing.models import Bill
            from apps.patients.models import Patient
            
            patient = Patient.objects.get(user=user)
            today = timezone.now().date()
            
            # Patient's upcoming appointments
            upcoming_appointments = Appointment.objects.filter(
                patient=patient,
                appointment_date__gte=today,
                status__in=['SCHEDULED', 'CONFIRMED']
            ).select_related('doctor').order_by('appointment_date', 'appointment_time')[:5]
            
            # Patient's pending bills
            pending_bills = Bill.objects.filter(
                patient=patient,
                status__in=['PENDING', 'PARTIAL']
            ).order_by('-created_at')[:3]
            
            return {
                'upcoming_appointments': upcoming_appointments,
                'pending_bills': pending_bills,
                'total_upcoming_appointments': upcoming_appointments.count(),
                'total_pending_bills': pending_bills.count(),
                'patient_profile': patient,
                'dashboard_type': 'patient'
            }
            
        except Exception as e:
            logger.error(f"Error getting patient dashboard context: {e}")
            return {
                'upcoming_appointments': [],
                'pending_bills': [],
                'total_upcoming_appointments': 0,
                'total_pending_bills': 0,
                'dashboard_type': 'patient'
            }
    
    def _get_staff_context(self, user):
        """Get staff dashboard context"""
        try:
            from apps.appointments.models import Appointment
            
            today = timezone.now().date()
            
            # General staff metrics
            appointments_today = Appointment.objects.filter(
                appointment_date=today
            ).count()
            
            waiting_patients = Appointment.objects.filter(
                appointment_date=today,
                status='SCHEDULED'
            ).count()
            
            return {
                'appointments_today': appointments_today,
                'waiting_patients': waiting_patients,
                'dashboard_type': 'staff'
            }
            
        except Exception as e:
            logger.error(f"Error getting staff dashboard context: {e}")
            return {'dashboard_type': 'staff'}


# API Views for Dynamic Updates
class DashboardAPIView(LoginRequiredMixin, View):
    """Base API view for dashboard endpoints"""
    
    def dispatch(self, request, *args, **kwargs):
        """Check for HTMX/AJAX requests"""
        if not (request.headers.get('HX-Request') or request.headers.get('X-Requested-With') == 'XMLHttpRequest'):
            return JsonResponse({'error': 'API request required'}, status=400)
        return super().dispatch(request, *args, **kwargs)


class DashboardStatsAPIView(DashboardAPIView):
    """API endpoint for dashboard statistics"""
    
    @method_decorator(cache_page(60))  # Cache for 1 minute
    def get(self, request):
        """Get updated dashboard statistics"""
        user = request.user
        
        try:
            if user.role in ['ADMIN', 'SUPERADMIN']:
                # Get admin metrics
                patient_metrics = DashboardMetricsService.get_patient_metrics(user)
                appointment_metrics = DashboardMetricsService.get_appointment_metrics(user)
                revenue_metrics = DashboardMetricsService.get_revenue_metrics(user)
                staff_metrics = DashboardMetricsService.get_staff_metrics(user)
                
                data = {
                    'patients': patient_metrics,
                    'appointments': appointment_metrics,
                    'revenue': revenue_metrics,
                    'staff': staff_metrics
                }
                
                # Return HTML for HTMX or JSON for AJAX
                if request.headers.get('HX-Request'):
                    # Provide both nested metrics and flat keys for backward compatibility
                    html = render_to_string('dashboard/partials/kpi_cards.html', {
                        'patient_metrics': patient_metrics,
                        'appointment_metrics': appointment_metrics,
                        'revenue_metrics': revenue_metrics,
                        'staff_metrics': staff_metrics,
                        # flat keys used by legacy snippets within the partial
                        'total_patients': patient_metrics.get('total', 0),
                        'new_patients_today': patient_metrics.get('new_today', 0),
                        'total_doctors': staff_metrics.get('doctors', 0),
                        'total_nurses': staff_metrics.get('nurses', 0),
                        'today_appointments': appointment_metrics.get('today_total', 0),
                        'pending_appointments': appointment_metrics.get('today_pending', 0),
                        'revenue_today': revenue_metrics.get('today', 0),
                        'revenue_month': revenue_metrics.get('month', 0),
                        'total_staff': staff_metrics.get('total', 0),
                    })
                    return HttpResponse(html)
                else:
                    return JsonResponse(data)
            
            else:
                return JsonResponse({'error': 'Unauthorized'}, status=403)
                
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)


class DashboardActivitiesAPIView(DashboardAPIView):
    """API endpoint for recent activities"""
    
    @method_decorator(cache_page(30))  # Cache for 30 seconds
    def get(self, request):
        """Get recent activities"""
        try:
            activities = DashboardActivityService.get_recent_activities(request.user, 10)
            
            if request.headers.get('HX-Request'):
                html = render_to_string('dashboard/partials/activity_feed.html', {
                    'recent_activities': activities
                })
                return HttpResponse(html)
            else:
                return JsonResponse({'activities': activities})
                
        except Exception as e:
            logger.error(f"Error getting activities: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)


class DashboardTasksAPIView(DashboardAPIView):
    """API endpoint for pending tasks"""
    
    @method_decorator(cache_page(60))  # Cache for 1 minute
    def get(self, request):
        """Get pending tasks"""
        try:
            tasks = DashboardActivityService.get_pending_tasks(request.user)
            
            if request.headers.get('HX-Request'):
                html = render_to_string('dashboard/partials/pending_tasks.html', {
                    'pending_tasks': tasks
                })
                return HttpResponse(html)
            else:
                return JsonResponse({'tasks': tasks})
                
        except Exception as e:
            logger.error(f"Error getting tasks: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)


class DashboardChartsAPIView(DashboardAPIView):
    """API endpoint for chart data"""
    
    @method_decorator(cache_page(300))  # Cache for 5 minutes
    def get(self, request):
        """Get chart data"""
        chart_type = request.GET.get('type', 'revenue')
        days = int(request.GET.get('days', 7))
        
        try:
            if chart_type == 'revenue':
                data = DashboardChartService.get_revenue_chart_data(days)
            elif chart_type == 'appointments':
                data = DashboardChartService.get_appointments_chart_data(days)
            elif chart_type == 'patients':
                data = DashboardChartService.get_patient_registration_chart_data(days)
            else:
                return JsonResponse({'error': 'Invalid chart type'}, status=400)
            
            if request.headers.get('HX-Request'):
                # Normalize data to labels/values expected by the chart partial
                labels = [d.get('label') for d in data]
                values = [d.get('value') for d in data]
                chart_data = json.dumps({'labels': labels, 'values': values})

                # Pick chart id and dataset label based on type
                chart_id = 'revenueChart' if chart_type == 'revenue' else (
                    'appointmentsChart' if chart_type == 'appointments' else 'patientsChart'
                )
                dataset_label = 'Revenue' if chart_type == 'revenue' else (
                    'Appointments' if chart_type == 'appointments' else 'Patients'
                )

                # Return rendered chart component using a generic partial
                html = render_to_string('dashboard/partials/chart_data.html', {
                    'chart_data': chart_data,
                    'chart_id': chart_id,
                    'dataset_label': dataset_label,
                    'is_currency': True if chart_type == 'revenue' else False,
                })
                return HttpResponse(html)
            else:
                return JsonResponse({'chart_data': data})
                
        except Exception as e:
            logger.error(f"Error getting chart data: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)


# Dashboard Management Views
class DashboardSettingsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Dashboard settings and configuration"""
    template_name = 'dashboard/settings.html'
    
    def test_func(self):
        return is_admin_user(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'widgets': DashboardWidget.objects.filter(is_active=True),
            'user_layout': self.request.user.dashboard_layout,
        })
        return context


class DashboardLayoutAPIView(LoginRequiredMixin, View):
    """API for saving dashboard layout preferences"""
    
    @require_http_methods(["POST"])
    def post(self, request):
        """Save user dashboard layout"""
        try:
            data = json.loads(request.body)
            layout, created = UserDashboardLayout.objects.get_or_create(
                user=request.user,
                defaults={'layout_config': {}}
            )
            
            # Update layout configuration
            if 'layout_config' in data:
                layout.layout_config = data['layout_config']
            if 'widget_settings' in data:
                layout.widget_settings = data['widget_settings']
            if 'theme' in data:
                layout.theme = data['theme']
            if 'sidebar_collapsed' in data:
                layout.sidebar_collapsed = data['sidebar_collapsed']
            
            layout.save()
            
            # Log activity
            ActivityLog.log_activity(
                user=request.user,
                action='dashboard_layout_updated',
                description='Updated dashboard layout preferences',
                request=request
            )
            
            return JsonResponse({'status': 'success'})
            
        except Exception as e:
            logger.error(f"Error saving dashboard layout: {e}")
            return JsonResponse({'error': 'Failed to save layout'}, status=500)


# Analytics Views
class DashboardAnalyticsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Dashboard analytics and usage statistics"""
    template_name = 'dashboard/analytics.html'
    
    def test_func(self):
        return is_admin_user(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get analytics data
        try:
            # User activity analytics
            active_users = CustomUser.objects.filter(
                last_login__gte=timezone.now() - timedelta(days=30)
            ).count()
            
            # Most active users
            most_active = DashboardAnalytics.objects.values('user__first_name', 'user__last_name') \
                .annotate(views=Count('id')) \
                .order_by('-views')[:10]
            
            context.update({
                'active_users': active_users,
                'most_active_users': most_active,
            })
            
        except Exception as e:
            logger.error(f"Error getting analytics data: {e}")
            context.update({
                'active_users': 0,
                'most_active_users': [],
            })
        
        return context


# Legacy function-based views for backward compatibility
@login_required
def dashboard_home(request):
    """Legacy function-based dashboard view"""
    view = DashboardHomeView()
    view.request = request
    return view.dispatch(request)


# HTMX Views (keeping existing naming for compatibility)
@login_required
def htmx_dashboard_stats(request):
    """HTMX endpoint for dashboard statistics"""
    view = DashboardStatsAPIView()
    view.request = request
    return view.dispatch(request)


@login_required
def htmx_recent_activities(request):
    """HTMX endpoint for recent activities"""
    view = DashboardActivitiesAPIView()
    view.request = request
    return view.dispatch(request)


@login_required
def htmx_pending_tasks(request):
    """HTMX endpoint for pending tasks"""
    view = DashboardTasksAPIView()
    view.request = request
    return view.dispatch(request)


@login_required
def htmx_chart_data(request):
    """HTMX endpoint for chart data"""
    view = DashboardChartsAPIView()
    view.request = request
    return view.dispatch(request)


# Additional Dashboard Views

class DashboardActivityView(LoginRequiredMixin, TemplateView):
    """Dashboard activity log view"""
    template_name = 'dashboard/activity_log.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Use classmethod-based service API
        activities = DashboardActivityService.get_recent_activities(self.request.user, limit=50)
        
        # Paginate activities
        paginator = Paginator(activities, 20)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context.update({
            'activities': page_obj,
            'total_activities': len(activities),
        })
        return context


class DashboardSearchView(LoginRequiredMixin, TemplateView):
    """Global search functionality"""
    template_name = 'dashboard/search_results.html'
    
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '').strip()
        if not query:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'results': []})
            return render(request, 'dashboard/search.html')
        
        # Perform search across multiple models
        results = self.perform_search(query, request.user)
        
        # Return JSON for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'results': results})
        
        context = {
            'query': query,
            'results': results,
        }
        return render(request, self.template_name, context)
    
    def perform_search(self, query, user):
        """Perform search across different models based on user permissions"""
        from django.db.models import Q
        from apps.patients.models import Patient
        from apps.appointments.models import Appointment
        from apps.doctors.models import Doctor
        from apps.nurses.models import Nurse
        from apps.staff.models import Staff
        
        results = []
        query_lower = query.lower()
        
        try:
            # Search Patients (if user has permission)
            if user.role in ['SUPERADMIN', 'ADMIN', 'DOCTOR', 'NURSE', 'RECEPTIONIST']:
                patients = Patient.objects.filter(
                    Q(first_name__icontains=query) |
                    Q(last_name__icontains=query) |
                    Q(email__icontains=query) |
                    Q(phone_number__icontains=query) |
                    Q(patient_id__icontains=query)
                ).select_related()[:5]
                
                for patient in patients:
                    results.append({
                        'category': 'Patient',
                        'title': f"{patient.first_name} {patient.last_name}",
                        'description': f"ID: {patient.patient_id} | Phone: {patient.phone_number}",
                        'url': f'/en/patients/{patient.id}/'
                    })
            
            # Search Doctors (if user has permission)
            if user.role in ['SUPERADMIN', 'ADMIN']:
                doctors = Doctor.objects.filter(
                    Q(user__first_name__icontains=query) |
                    Q(user__last_name__icontains=query) |
                    Q(specialization__name__icontains=query) |
                    Q(license_number__icontains=query)
                ).select_related('user', 'specialization')[:5]
                
                for doctor in doctors:
                    results.append({
                        'category': 'Doctor',
                        'title': f"Dr. {doctor.user.first_name} {doctor.user.last_name}",
                        'description': f"Specialization: {doctor.specialization.name if doctor.specialization else 'General'}",
                        'url': f'/en/doctors/{doctor.id}/'
                    })
            
            # Search Appointments (if user has permission)
            if user.role in ['SUPERADMIN', 'ADMIN', 'DOCTOR', 'NURSE', 'RECEPTIONIST']:
                appointments = Appointment.objects.filter(
                    Q(patient__first_name__icontains=query) |
                    Q(patient__last_name__icontains=query) |
                    Q(doctor__user__first_name__icontains=query) |
                    Q(doctor__user__last_name__icontains=query) |
                    Q(appointment_type__icontains=query)
                ).select_related('patient', 'doctor__user')[:5]
                
                for appointment in appointments:
                    results.append({
                        'category': 'Appointment',
                        'title': f"{appointment.patient.first_name} {appointment.patient.last_name} - Dr. {appointment.doctor.user.first_name}",
                        'description': f"Date: {appointment.appointment_date} | Type: {appointment.appointment_type}",
                        'url': f'/en/appointments/{appointment.id}/'
                    })
            
            # Search Staff (if user has admin permissions)
            if user.role in ['SUPERADMIN', 'ADMIN']:
                staff_members = Staff.objects.filter(
                    Q(user__first_name__icontains=query) |
                    Q(user__last_name__icontains=query) |
                    Q(department__icontains=query) |
                    Q(position__icontains=query)
                ).select_related('user')[:5]
                
                for staff in staff_members:
                    results.append({
                        'category': 'Staff',
                        'title': f"{staff.user.first_name} {staff.user.last_name}",
                        'description': f"Department: {staff.department} | Position: {staff.position}",
                        'url': f'/en/staff/{staff.id}/'
                    })
        
        except Exception as e:
            logger.error(f"Search error: {e}")
            
        return results[:15]  # Limit to 15 results


class DashboardExportView(LoginRequiredMixin, View):
    """Data export functionality"""
    
    def get(self, request, *args, **kwargs):
        export_type = request.GET.get('type', 'csv')
        data_type = request.GET.get('data', 'stats')
        
        try:
            if data_type == 'stats':
                metrics_service = DashboardMetricsService(request.user)
                data = metrics_service.get_dashboard_stats()
            else:
                data = {}
            
            if export_type == 'json':
                response = JsonResponse(data)
                response['Content-Disposition'] = f'attachment; filename="dashboard_{data_type}.json"'
                return response
            
            # Default to CSV
            import csv
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="dashboard_{data_type}.csv"'
            
            writer = csv.writer(response)
            # Add CSV writing logic here
            writer.writerow(['Key', 'Value'])
            for key, value in data.items():
                writer.writerow([key, value])
            
            return response
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            messages.error(request, "Export failed. Please try again.")
            return redirect('dashboard:home')


class DashboardProfileView(LoginRequiredMixin, TemplateView):
    """User profile management"""
    template_name = 'dashboard/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context


class DashboardNotificationsAPIView(LoginRequiredMixin, View):
    """API endpoint for notifications"""
    
    def get(self, request):
        try:
            # This would integrate with a notifications system
            notifications = []  # Placeholder
            
            return JsonResponse({
                'success': True,
                'notifications': notifications,
                'unread_count': 0,
            })
            
        except Exception as e:
            logger.error(f"Failed to fetch notifications: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Failed to load notifications'
            }, status=500)


class MarkNotificationReadView(LoginRequiredMixin, View):
    """Mark notification as read"""
    
    def post(self, request, notification_id):
        try:
            # Mark notification as read logic here
            return JsonResponse({'success': True})
        except Exception as e:
            logger.error(f"Failed to mark notification as read: {e}")
            return JsonResponse({'success': False}, status=500)


class MarkAllNotificationsReadView(LoginRequiredMixin, View):
    """Mark all notifications as read"""
    
    def post(self, request):
        try:
            # Mark all notifications as read logic here
            return JsonResponse({'success': True})
        except Exception as e:
            logger.error(f"Failed to mark all notifications as read: {e}")
            return JsonResponse({'success': False}, status=500)


class NotificationListView(LoginRequiredMixin, TemplateView):
    """List all notifications"""
    template_name = 'dashboard/notifications_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add notifications data
        context['notifications'] = []  # Placeholder
        return context


class NotificationSettingsView(LoginRequiredMixin, TemplateView):
    """Notification preferences"""
    template_name = 'dashboard/notification_settings.html'


class SystemConfigView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """System configuration view"""
    template_name = 'dashboard/system_config.html'
    
    def test_func(self):
        return is_admin_user(self.request.user)


class SystemMaintenanceView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """System maintenance view"""
    template_name = 'dashboard/system_maintenance.html'
    
    def test_func(self):
        return is_admin_user(self.request.user)


class SystemBackupView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """System backup view"""
    template_name = 'dashboard/system_backup.html'
    
    def test_func(self):
        return is_admin_user(self.request.user)