# apps/core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse, Http404
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.template.loader import render_to_string
from django.db.models import Count, Q, Sum
from django.utils import timezone
from django.views.decorators.csrf import requires_csrf_token
from django.views.decorators.cache import never_cache
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
# from tenants.models import Tenant  # Temporarily commented
from apps.staff.models import Department
from apps.patients.models import Patient
from apps.appointments.models import Appointment
from apps.billing.models import Bill
# Note: EmergencyCase import removed as emergency cases don't have tenant relationship
from .models import Notification, ActivityLog, SystemConfiguration
import json
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


@requires_csrf_token
def csrf_failure(request, reason=""):
    """Custom CSRF failure view"""
    logger.warning(f"CSRF failure from {request.META.get('REMOTE_ADDR')}: {reason}")
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'error': 'CSRF token missing or incorrect',
            'code': 'csrf_failure'
        }, status=403)
    
    return render(request, 'errors/403_csrf.html', {
        'reason': reason
    }, status=403)


def handler403(request, exception=None):
    """Custom 403 error handler"""
    logger.warning(f"403 Forbidden: {request.path} from {request.META.get('REMOTE_ADDR')}")
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'error': 'Access forbidden',
            'code': 'permission_denied'
        }, status=403)
    
    return render(request, 'errors/403.html', status=403)


def handler404(request, exception=None):
    """Custom 404 error handler"""
    logger.info(f"404 Not Found: {request.path}")
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'error': 'Resource not found',
            'code': 'not_found'
        }, status=404)
    
    return render(request, 'errors/404.html', status=404)


def handler500(request):
    """Custom 500 error handler"""
    logger.error(f"500 Internal Server Error: {request.path}")
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'error': 'Internal server error',
            'code': 'server_error'
        }, status=500)
    
    return render(request, 'errors/500.html', status=500)


@never_cache
def security_headers_test(request):
    """Test endpoint for security headers"""
    response = JsonResponse({
        'message': 'Security headers test',
        'timestamp': timezone.now().isoformat()
    })
    
    # Add additional security headers for testing
    response['X-Test-Header'] = 'security-test'
    
    return response


def home_redirect(request):
    """Redirect home to appropriate dashboard"""
    if request.user.is_authenticated:
    # Do not auto-select a tenant; selection is enforced by middleware on module access
    # For regular users with a single assigned tenant, middleware will set context when needed
        
        return redirect('dashboard:home')
    return redirect('accounts:login')


class DashboardView(LoginRequiredMixin, TemplateView):
    """Main dashboard view with unified template"""
    template_name = 'dashboard/unified_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        tenant = getattr(self.request, 'tenant', None)
        
        if not tenant:
            return context
            
        # Get date ranges
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        
        # Base queryset filters
        tenant_filter = {'tenant': tenant}
        
        # Patient-specific filters (uses registration_date)
        patient_today_filter = {**tenant_filter, 'registration_date__date': today}
        patient_week_filter = {**tenant_filter, 'registration_date__date__gte': week_start}
        patient_month_filter = {**tenant_filter, 'registration_date__date__gte': month_start}
        
        # General filters for models with created_at
        today_filter = {**tenant_filter, 'created_at__date': today}
        week_filter = {**tenant_filter, 'created_at__date__gte': week_start}
        month_filter = {**tenant_filter, 'created_at__date__gte': month_start}
        
        # Dashboard statistics based on user role
        if user.role in ['ADMIN', 'SUPERADMIN'] or user.is_superuser:
            context.update(self._get_admin_stats(
                tenant_filter, patient_today_filter, patient_week_filter, patient_month_filter, today_filter
            ))
        elif user.role == 'DOCTOR':
            context.update(self._get_doctor_stats(user, tenant_filter, today))
        elif user.role == 'NURSE':
            context.update(self._get_nurse_stats(user, tenant_filter, today_filter))
        elif user.role == 'RECEPTIONIST':
            context.update(self._get_receptionist_stats(tenant_filter, today))
        
        # Common context for all roles
        context.update({
            'recent_notifications': Notification.objects.filter(
                recipient=user, tenant=tenant
            ).order_by('-created_at')[:5],
            'unread_notifications_count': Notification.objects.filter(
                recipient=user, tenant=tenant, is_read=False
            ).count(),
            'tenant': tenant,
            'user_role': user.role,
            'today': today,
        })
        
        return context
    
    def _get_admin_stats(self, tenant_filter, patient_today_filter, patient_week_filter, patient_month_filter, today_filter):
        """Get statistics for admin users"""
        # Extract today date for appointment filtering
        today_date = patient_today_filter['registration_date__date']
        
        return {
            'total_patients': Patient.objects.filter(**tenant_filter).count(),
            'new_patients_today': Patient.objects.filter(**patient_today_filter).count(),
            'new_patients_week': Patient.objects.filter(**patient_week_filter).count(),
            'new_patients_month': Patient.objects.filter(**patient_month_filter).count(),
            
            'total_appointments': Appointment.objects.filter(**tenant_filter).count(),
            'appointments_today': Appointment.objects.filter(
                tenant=tenant_filter['tenant'], 
                appointment_date=today_date
            ).count(),
            'pending_appointments': Appointment.objects.filter(
                **tenant_filter, status='SCHEDULED'
            ).count(),
            
            'total_doctors': User.objects.filter(**tenant_filter, role='DOCTOR', is_active=True).count(),
            'total_nurses': User.objects.filter(**tenant_filter, role='NURSE', is_active=True).count(),
            'total_staff': User.objects.filter(**tenant_filter, is_active=True).exclude(role='PATIENT').count(),
            
            # Note: Emergency cases not included as they don't have tenant relationship
            # 'emergency_cases_today': EmergencyCase.objects.filter(**today_filter).count(),
            # 'active_emergency_cases': EmergencyCase.objects.filter(
            #     **tenant_filter, status__in=['WAITING', 'IN_PROGRESS']
            # ).count(),
            
            'revenue_today': Bill.objects.filter(**today_filter, status='PAID').aggregate(
                total=Sum('total_amount')
            )['total'] or 0,
            'revenue_month': Bill.objects.filter(
                tenant=tenant_filter['tenant'], 
                created_at__date__gte=patient_month_filter['registration_date__date__gte'],
                status='PAID'
            ).aggregate(
                total=Sum('total_amount')
            )['total'] or 0,
            'pending_bills': Bill.objects.filter(**tenant_filter, status='PENDING').count(),
            
            'departments': Department.objects.filter(**tenant_filter, is_active=True)[:5],
            'recent_activities': ActivityLog.objects.filter(**tenant_filter).order_by('-timestamp')[:10],
        }
    
    def _get_doctor_stats(self, user, tenant_filter, today_date):
        """Get statistics for doctor users"""
        doctor_appointments = Appointment.objects.filter(doctor=user, **tenant_filter)
        
        return {
            'my_appointments_today': doctor_appointments.filter(
                appointment_date=today_date
            ).count(),
            'my_total_appointments': doctor_appointments.count(),
            'my_pending_appointments': doctor_appointments.filter(status='SCHEDULED').count(),
            'my_completed_appointments': doctor_appointments.filter(status='COMPLETED').count(),
            'my_patients': doctor_appointments.values('patient').distinct().count(),
            'upcoming_appointments': doctor_appointments.filter(
                appointment_date__gte=timezone.now().date(),
                status='SCHEDULED'
            ).order_by('appointment_date', 'appointment_time')[:5],
        }
    
    def _get_nurse_stats(self, user, tenant_filter, today_filter):
        """Get statistics for nurse users"""
        return {
            # Note: Emergency cases not included as they don't have tenant relationship
            # 'emergency_cases_today': EmergencyCase.objects.filter(**today_filter).count(),
            # 'active_emergency_cases': EmergencyCase.objects.filter(
            #     **tenant_filter, status__in=['WAITING', 'IN_PROGRESS']
            # ).count(),
            'patients_assigned': Patient.objects.filter(
                **tenant_filter, assigned_nurse=user
            ).count(),
        }
    
    def _get_receptionist_stats(self, tenant_filter, today_date):
        """Get statistics for receptionist users"""
        return {
            'appointments_today': Appointment.objects.filter(
                tenant=tenant_filter['tenant'], 
                appointment_date=today_date
            ).count(),
            'pending_appointments': Appointment.objects.filter(
                **tenant_filter, status='SCHEDULED'
            ).count(),
            'walk_in_patients_today': Patient.objects.filter(
                tenant=tenant_filter['tenant'],
                registration_date__date=today_date, 
                registration_type='WALK_IN'
            ).count(),
            'pending_bills': Bill.objects.filter(**tenant_filter, status='PENDING').count(),
        }


class NotificationListView(LoginRequiredMixin, ListView):
    """List user notifications"""
    model = Notification
    template_name = 'core/notifications.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user,
            tenant=getattr(self.request, 'tenant', None)
        ).order_by('-created_at')


@login_required
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    notification = get_object_or_404(
        Notification, 
        id=notification_id, 
        recipient=request.user
    )
    notification.mark_as_read()
    
    if request.headers.get('HX-Request'):
        return HttpResponse(status=204)
    
    return JsonResponse({'status': 'success'})


@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read for the current user"""
    Notification.objects.filter(
        recipient=request.user,
        tenant=getattr(request, 'tenant', None),
        is_read=False
    ).update(is_read=True, read_at=timezone.now())
    
    if request.headers.get('HX-Request'):
        return HttpResponse(status=204)
    
    return JsonResponse({'status': 'success'})


@login_required
def get_notifications(request):
    """AJAX endpoint to get notifications"""
    notifications = Notification.objects.filter(
        recipient=request.user,
        tenant=getattr(request, 'tenant', None)
    ).order_by('-created_at')[:10]
    
    data = []
    for notification in notifications:
        data.append({
            'id': str(notification.id),
            'title': notification.title,
            'message': notification.message,
            'type': notification.type,
            'priority': notification.priority,
            'is_read': notification.is_read,
            'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M'),
            'link': notification.link,
        })
    
    return JsonResponse({
        'notifications': data,
        'unread_count': notifications.filter(is_read=False).count()
    })


class ActivityLogView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """View activity logs (Admin only)"""
    model = ActivityLog
    template_name = 'core/activity_logs.html'
    context_object_name = 'activities'
    paginate_by = 50
    
    def test_func(self):
        return self.request.user.role in ['ADMIN', 'SUPERADMIN'] or self.request.user.is_superuser
    
    def get_queryset(self):
        # ActivityLog has no tenant field; rely on db routing/user filters
        queryset = ActivityLog.objects.all().order_by('-timestamp')
        
        # Filter by user if specified
        user_id = self.request.GET.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by action if specified
        action = self.request.GET.get('action')
        if action:
            queryset = queryset.filter(action=action)
            
        # Filter by date range
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            queryset = queryset.filter(timestamp__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__date__lte=date_to)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
        context['selected_user'] = self.request.GET.get('user', '')
        context['selected_action'] = self.request.GET.get('action', '')
        return context


class SystemConfigurationView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """System configuration view (Hospital Admin only; requires selected hospital)"""
    model = SystemConfiguration
    template_name = 'core/system_config.html'
    fields = [
        'tenant_name', 'tenant_logo', 'contact_email', 'contact_phone', 'address',
        'consultation_fee', 'currency_code', 'tax_rate',
        'appointment_duration', 'advance_booking_days', 'cancellation_hours',
        'patient_id_prefix', 'auto_generate_patient_id',
        'email_notifications', 'sms_notifications', 'whatsapp_notifications',
        'auto_backup', 'backup_frequency'
    ]
    success_url = reverse_lazy('dashboard:system_config')
    
    def test_func(self):
        # Only hospital admins (role ADMIN) can edit system settings
        # SUPERADMIN must select hospital first and then only ADMIN role can access
        user_role = getattr(self.request.user, 'role', '')
        return user_role == 'ADMIN'

    def dispatch(self, request, *args, **kwargs):
        if not request.session.get('selected_hospital_code'):
            messages.info(request, 'Please select a hospital first.')
            return redirect('tenants:hospital_selection')
        return super().dispatch(request, *args, **kwargs)
    
    def get_object(self, queryset=None):
        # Use session-selected hospital to scope settings logically
        sel_code = self.request.session.get('selected_hospital_code')
        if not sel_code:
            raise Http404("Hospital not selected")
        # Try to find config by tenant_name == code; else create default
        obj = SystemConfiguration.objects.filter(tenant_name=sel_code).first()
        if not obj:
            obj = SystemConfiguration.objects.create(
                tenant_name=sel_code,
                contact_email=self.request.user.email or '',
                contact_phone='',
                address='',
            )
        return obj
    
    def form_valid(self, form):
        # Ensure tenant_name follows the selected hospital for grouping
        sel_code = self.request.session.get('selected_hospital_code')
        if not sel_code:
            raise Http404("Hospital not selected")
        form.instance.tenant_name = sel_code
        messages.success(self.request, 'System configuration updated successfully.')
        return super().form_valid(form)


@login_required
def search_global(request):
    """Global search functionality"""
    query = request.GET.get('q', '').strip()
    if not query or len(query) < 2:
        return JsonResponse({'results': []})
    
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return JsonResponse({'results': []})
    
    results = []
    
    # Search patients
    patients = Patient.objects.filter(
        tenant=tenant,
        first_name__icontains=query
    ) | Patient.objects.filter(
        tenant=tenant,
        last_name__icontains=query
    ) | Patient.objects.filter(
        tenant=tenant,
        patient_id__icontains=query
    )
    
    for patient in patients[:5]:
        results.append({
            'type': 'patient',
            'id': str(patient.id),
            'title': patient.get_full_name(),
            'subtitle': f"ID: {patient.patient_id}",
            'url': f'/patients/{patient.id}/'
        })
    
    # Search doctors
    if request.user.has_module_permission('doctors'):
        doctors = User.objects.filter(
            tenant=tenant,
            role='DOCTOR',
            first_name__icontains=query
        ) | User.objects.filter(
            tenant=tenant,
            role='DOCTOR',
            last_name__icontains=query
        )
        
        for doctor in doctors[:5]:
            results.append({
                'type': 'doctor',
                'id': str(doctor.id),
                'title': doctor.get_display_name(),
                'subtitle': doctor.specialization or 'Doctor',
                'url': f'/doctors/{doctor.id}/'
            })
    
    # Search appointments
    if request.user.has_module_permission('appointments'):
        appointments = Appointment.objects.filter(
            tenant=tenant,
            patient__first_name__icontains=query
        ) | Appointment.objects.filter(
            tenant=tenant,
            patient__last_name__icontains=query
        )
        
        for appointment in appointments[:3]:
            results.append({
                'type': 'appointment',
                'id': str(appointment.id),
                'title': f"Appointment - {appointment.patient.get_full_name()}",
                'subtitle': f"{appointment.appointment_date} at {appointment.appointment_time}",
                'url': f'/appointments/{appointment.id}/'
            })
    
    return JsonResponse({'results': results})


@login_required
def export_data(request):
    """Export data functionality (Admin only)"""
    if not (request.user.role in ['ADMIN', 'SUPERADMIN'] or request.user.is_superuser):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    export_type = request.GET.get('type')
    tenant = getattr(request, 'tenant', None)
    
    if not tenant:
        return JsonResponse({'error': 'Tenant not found'}, status=400)
    
    # This is a placeholder - you would implement actual export logic
    return JsonResponse({
        'status': 'success',
        'message': f'Export of {export_type} data initiated. You will receive an email when ready.'
    })


class ProfileView(LoginRequiredMixin, TemplateView):
    """User profile view"""
    template_name = 'core/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['user'] = user
        # ActivityLog no longer stores tenant as a direct FK. Fetch recent
        # activities for the user only to avoid field errors.
        context['recent_activities'] = ActivityLog.objects.filter(
            user=user
        ).order_by('-timestamp')[:10]
        return context
