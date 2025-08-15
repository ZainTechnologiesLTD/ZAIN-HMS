# apps/core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from apps.accounts.models import Hospital, Department
from apps.patients.models import Patient
from apps.appointments.models import Appointment
from apps.billing.models import Bill
from apps.emergency.models import EmergencyCase
from .models import Notification, ActivityLog, SystemConfiguration
import json

User = get_user_model()


def home_redirect(request):
    """Redirect home to appropriate dashboard"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    return redirect('accounts:login')


class DashboardView(LoginRequiredMixin, TemplateView):
    """Main dashboard view with hospital statistics"""
    template_name = 'core/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        hospital = getattr(self.request, 'hospital', None)
        
        if not hospital:
            return context
            
        # Get date ranges
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        
        # Base queryset filters
        hospital_filter = {'hospital': hospital}
        today_filter = {**hospital_filter, 'created_at__date': today}
        week_filter = {**hospital_filter, 'created_at__date__gte': week_start}
        month_filter = {**hospital_filter, 'created_at__date__gte': month_start}
        
        # Dashboard statistics based on user role
        if user.role in ['ADMIN', 'SUPERADMIN'] or user.is_superuser:
            context.update(self._get_admin_stats(hospital_filter, today_filter, week_filter, month_filter))
        elif user.role == 'DOCTOR':
            context.update(self._get_doctor_stats(user, hospital_filter, today_filter))
        elif user.role == 'NURSE':
            context.update(self._get_nurse_stats(user, hospital_filter, today_filter))
        elif user.role == 'RECEPTIONIST':
            context.update(self._get_receptionist_stats(hospital_filter, today_filter))
        
        # Common context for all roles
        context.update({
            'recent_notifications': Notification.objects.filter(
                recipient=user, hospital=hospital
            ).order_by('-created_at')[:5],
            'unread_notifications_count': Notification.objects.filter(
                recipient=user, hospital=hospital, is_read=False
            ).count(),
            'hospital': hospital,
            'user_role': user.role,
            'today': today,
        })
        
        return context
    
    def _get_admin_stats(self, hospital_filter, today_filter, week_filter, month_filter):
        """Get statistics for admin users"""
        return {
            'total_patients': Patient.objects.filter(**hospital_filter).count(),
            'new_patients_today': Patient.objects.filter(**today_filter).count(),
            'new_patients_week': Patient.objects.filter(**week_filter).count(),
            'new_patients_month': Patient.objects.filter(**month_filter).count(),
            
            'total_appointments': Appointment.objects.filter(**hospital_filter).count(),
            'appointments_today': Appointment.objects.filter(
                hospital=hospital_filter['hospital'], 
                appointment_date=today_filter['created_at__date']
            ).count(),
            'pending_appointments': Appointment.objects.filter(
                **hospital_filter, status='SCHEDULED'
            ).count(),
            
            'total_doctors': User.objects.filter(**hospital_filter, role='DOCTOR', is_active=True).count(),
            'total_nurses': User.objects.filter(**hospital_filter, role='NURSE', is_active=True).count(),
            'total_staff': User.objects.filter(**hospital_filter, is_active=True).exclude(role='PATIENT').count(),
            
            'emergency_cases_today': EmergencyCase.objects.filter(**today_filter).count(),
            'active_emergency_cases': EmergencyCase.objects.filter(
                **hospital_filter, status__in=['WAITING', 'IN_PROGRESS']
            ).count(),
            
            'revenue_today': Bill.objects.filter(**today_filter, status='PAID').aggregate(
                total=Sum('total_amount')
            )['total'] or 0,
            'revenue_month': Bill.objects.filter(**month_filter, status='PAID').aggregate(
                total=Sum('total_amount')
            )['total'] or 0,
            'pending_bills': Bill.objects.filter(**hospital_filter, status='PENDING').count(),
            
            'departments': Department.objects.filter(**hospital_filter, is_active=True)[:5],
            'recent_activities': ActivityLog.objects.filter(**hospital_filter).order_by('-timestamp')[:10],
        }
    
    def _get_doctor_stats(self, user, hospital_filter, today_filter):
        """Get statistics for doctor users"""
        doctor_appointments = Appointment.objects.filter(doctor=user, **hospital_filter)
        
        return {
            'my_appointments_today': doctor_appointments.filter(
                appointment_date=today_filter['created_at__date']
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
    
    def _get_nurse_stats(self, user, hospital_filter, today_filter):
        """Get statistics for nurse users"""
        return {
            'emergency_cases_today': EmergencyCase.objects.filter(**today_filter).count(),
            'active_emergency_cases': EmergencyCase.objects.filter(
                **hospital_filter, status__in=['WAITING', 'IN_PROGRESS']
            ).count(),
            'patients_assigned': Patient.objects.filter(
                **hospital_filter, assigned_nurse=user
            ).count(),
        }
    
    def _get_receptionist_stats(self, hospital_filter, today_filter):
        """Get statistics for receptionist users"""
        return {
            'appointments_today': Appointment.objects.filter(
                hospital=hospital_filter['hospital'], 
                appointment_date=today_filter['created_at__date']
            ).count(),
            'pending_appointments': Appointment.objects.filter(
                **hospital_filter, status='SCHEDULED'
            ).count(),
            'walk_in_patients_today': Patient.objects.filter(
                **today_filter, registration_type='WALK_IN'
            ).count(),
            'pending_bills': Bill.objects.filter(**hospital_filter, status='PENDING').count(),
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
            hospital=getattr(self.request, 'hospital', None)
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
        hospital=getattr(request, 'hospital', None),
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
        hospital=getattr(request, 'hospital', None)
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
        queryset = ActivityLog.objects.filter(
            hospital=getattr(self.request, 'hospital', None)
        ).order_by('-timestamp')
        
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
        context['users'] = User.objects.filter(
            hospital=getattr(self.request, 'hospital', None),
            is_active=True
        ).order_by('first_name', 'last_name')
        context['actions'] = ActivityLog.ACTION_CHOICES
        return context


class SystemConfigurationView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """System configuration view (Admin only)"""
    model = SystemConfiguration
    template_name = 'core/system_config.html'
    fields = [
        'hospital_name', 'hospital_logo', 'contact_email', 'contact_phone', 'address',
        'consultation_fee', 'currency_code', 'tax_rate',
        'appointment_duration', 'advance_booking_days', 'cancellation_hours',
        'patient_id_prefix', 'auto_generate_patient_id',
        'email_notifications', 'sms_notifications', 'whatsapp_notifications',
        'auto_backup', 'backup_frequency'
    ]
    success_url = reverse_lazy('core:system_config')
    
    def test_func(self):
        return self.request.user.role in ['ADMIN', 'SUPERADMIN'] or self.request.user.is_superuser
    
    def get_object(self, queryset=None):
        hospital = getattr(self.request, 'hospital', None)
        if hospital:
            obj, created = SystemConfiguration.objects.get_or_create(hospital=hospital)
            return obj
        return None
    
    def form_valid(self, form):
        messages.success(self.request, 'System configuration updated successfully.')
        return super().form_valid(form)


@login_required
def search_global(request):
    """Global search functionality"""
    query = request.GET.get('q', '').strip()
    if not query or len(query) < 2:
        return JsonResponse({'results': []})
    
    hospital = getattr(request, 'hospital', None)
    if not hospital:
        return JsonResponse({'results': []})
    
    results = []
    
    # Search patients
    patients = Patient.objects.filter(
        hospital=hospital,
        first_name__icontains=query
    ) | Patient.objects.filter(
        hospital=hospital,
        last_name__icontains=query
    ) | Patient.objects.filter(
        hospital=hospital,
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
            hospital=hospital,
            role='DOCTOR',
            first_name__icontains=query
        ) | User.objects.filter(
            hospital=hospital,
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
            hospital=hospital,
            patient__first_name__icontains=query
        ) | Appointment.objects.filter(
            hospital=hospital,
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
    hospital = getattr(request, 'hospital', None)
    
    if not hospital:
        return JsonResponse({'error': 'Hospital not found'}, status=400)
    
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
        context['recent_activities'] = ActivityLog.objects.filter(
            user=user, hospital=getattr(self.request, 'hospital', None)
        ).order_by('-timestamp')[:10]
        return context
