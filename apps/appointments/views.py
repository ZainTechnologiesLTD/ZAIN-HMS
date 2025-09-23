# apps/appointments/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponse
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters
from .models import Appointment
from .serializers import AppointmentSerializer
from apps.doctors.models import Doctor, DoctorSchedule
from datetime import datetime
from django.utils import timezone

# Add a custom filter set
class AppointmentFilter(filters.FilterSet):
    appointment_date = filters.DateFilter(field_name='datetime', lookup_expr='date')
    status = filters.CharFilter()
    patient = filters.NumberFilter()
    doctor = filters.NumberFilter()

    class Meta:
        model = Appointment
        fields = ['appointment_date', 'status', 'patient', 'doctor']

class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = AppointmentFilter

    def check_doctor_availability(self, doctor, date, time):
        schedules = DoctorSchedule.objects.filter(doctor=doctor, day_of_week=date.weekday())
        for schedule in schedules:
            if schedule.is_available(date, time):
                return True
        return False

    def perform_create(self, serializer):
        doctor = serializer.validated_data.get('doctor')
        date = serializer.validated_data.get('date')
        time = serializer.validated_data.get('time')
        if self.check_doctor_availability(doctor, date, time):
            serializer.save()
        else:
            raise serializers.ValidationError("The doctor is not available at this time.")

from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
import logging

# Get logger for security logging
logger = logging.getLogger(__name__)

from .models import Appointment, AppointmentType, AppointmentHistory
from .forms import (
    AppointmentForm, QuickAppointmentForm, AppointmentSearchForm,
    RescheduleAppointmentForm, CancelAppointmentForm
)
from apps.patients.models import Patient
from apps.doctors.models import Doctor, DoctorSchedule
from apps.core.utils.barcode_generator import DocumentBarcodeGenerator
from apps.core.permissions import (
    PatientAccessMixin, SecureViewMixin, audit_action, 
    patient_access_required, get_client_ip
)


# Compatibility helpers for existing URL names used elsewhere in the project.
def quick_schedule(request, *args, **kwargs):
    """Alias for quick_appointment_create used by urls.py elsewhere."""
    return quick_appointment_create(request, *args, **kwargs)


def check_availability(request, *args, **kwargs):
    """Alias for check_doctor_availability."""
    return check_doctor_availability(request, *args, **kwargs)


def get_doctor_schedule(request, *args, **kwargs):
    """Alias for get_available_time_slots."""
    return get_available_time_slots(request, *args, **kwargs)


@login_required
def get_doctors(request):
    """Return a JSON list of doctors.

    Expected query params:
    - q (optional) search string
    - department (optional) specialization filter
    - date (optional) date filter for availability
    """
    q = request.GET.get('q', '')
    department = request.GET.get('department', '')
    date_str = request.GET.get('date', '')
    
    doctors = Doctor.objects.filter(is_active=True)
    
    # Filter by search query
    if q:
        doctors = doctors.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(specialization__icontains=q)
        )
    
    # Filter by department (specialization)
    if department:
        doctors = doctors.filter(specialization=department)
    
    # If a date is provided, narrow to doctors who have an active schedule that day
    date_obj = None
    if date_str:
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        except Exception:
            date_obj = None
        if date_obj:
            day_of_week = date_obj.weekday()
            doctors = doctors.filter(schedules__day_of_week=day_of_week, schedules__is_active=True).distinct()
    
    data = []
    for d in doctors[:50]:
        available_slots = None
        if date_obj:
            # Calculate available blocks for the given date
            day_of_week = date_obj.weekday()
            schedules = DoctorSchedule.objects.filter(doctor=d, day_of_week=day_of_week, is_active=True)
            available_blocks = 0
            for schedule in schedules:
                capacity = schedule.max_patients or 1
                booked_qs = Appointment.objects.filter(
                    doctor=d,
                    appointment_date=date_obj,
                    appointment_time__gte=schedule.start_time,
                    appointment_time__lt=schedule.end_time,
                    status__in=['SCHEDULED', 'CONFIRMED', 'CHECKED_IN', 'IN_PROGRESS']
                )
                if getattr(schedule, 'break_start_time', None) and getattr(schedule, 'break_end_time', None):
                    booked_qs = booked_qs.exclude(
                        appointment_time__gte=schedule.break_start_time,
                        appointment_time__lt=schedule.break_end_time
                    )
                booked_count = booked_qs.count()
                if booked_count < capacity:
                    available_blocks += 1

            available_slots = available_blocks

        data.append({
            'id': str(d.id), 
            'name': d.get_full_name(), 
            'specialty': dict(Doctor.SPECIALIZATION_CHOICES).get(d.specialization, d.specialization),
            'specialization': d.specialization,
            # Provide available_slots so enhanced UI can display it
            **({'available_slots': available_slots} if available_slots is not None else {})
        })
    
    return JsonResponse({'results': data})


@login_required
def search_patients(request):
    """Enhanced patient search endpoint with pagination and better UX for large datasets."""
    q = request.GET.get('q', '').strip()
    page = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 20))  # Default 20 results per page
    
    # Ensure reasonable limits
    limit = min(limit, 100)  # Max 100 results per page
    limit = max(limit, 5)    # Min 5 results per page

    # Get all patients
    patients = Patient.objects.all()
    
    # Optional: keep results to active patients if model supports it
    try:
        patients = patients.filter(is_active=True)
    except Exception:
        # If field doesn't exist, ignore
        pass

    # Apply search filter if provided
    if q:
        patients = patients.filter(
            Q(first_name__icontains=q) | 
            Q(last_name__icontains=q) | 
            Q(phone__icontains=q) |
            Q(patient_id__icontains=q)  # Also search by patient ID
        ).distinct()
    
    # Order by most relevant first
    patients = patients.order_by('-updated_at', 'first_name', 'last_name')

    # Get total count before pagination
    total_count = patients.count()
    
    # Apply pagination
    offset = (page - 1) * limit
    paginated_patients = patients[offset:offset + limit]
    
    # Format response data with enhanced information
    data = []
    for p in paginated_patients:
        patient_data = {
            'id': str(p.id),
            'name': p.get_full_name(),
            'text': p.get_full_name(),  # For compatibility with existing code
            'phone': getattr(p, 'phone', '') or '',
            'email': getattr(p, 'email', '') or '',
            'patient_id': getattr(p, 'patient_id', '') or str(p.id)[:8],
            'age': getattr(p, 'age', None),
            'gender': getattr(p, 'gender', ''),
            'last_visit': str(getattr(p, 'last_visit', '')) if getattr(p, 'last_visit', None) else None,
        }
        data.append(patient_data)

    # Calculate pagination info
    total_pages = (total_count + limit - 1) // limit
    has_more = page < total_pages

    return JsonResponse({
        'success': True,
        'results': data,
        'pagination': {
            'current_page': page,
            'total_pages': total_pages,
            'total_count': total_count,
            'limit': limit,
            'has_more': has_more,
            'has_previous': page > 1,
        },
        'query': q
    })


@login_required
def patient_appointment_history(request, patient_id):
    """Return a simple JSON list of a patient's appointments (used by UI pages)."""
    appointments = Appointment.objects.filter(patient_id=patient_id).order_by('-appointment_date')[:100]
    data = [{
        'id': str(a.id),
        'date': a.appointment_date.isoformat() if a.appointment_date else None,
        'time': a.appointment_time.strftime('%H:%M') if a.appointment_time else None,
        'doctor': a.doctor.get_full_name() if a.doctor else None,
        'status': a.status,
        'chief_complaint': a.chief_complaint,
    } for a in appointments]
    return JsonResponse({'appointments': data})


@login_required
def upcoming_appointments(request):
    """Return a small list of upcoming appointments."""
    appointments = Appointment.objects.filter(appointment_date__gte=timezone.now().date()).order_by('appointment_date')[:50]
    data = [{
        'id': str(a.id),
        'date': a.appointment_date.isoformat() if a.appointment_date else None,
        'time': a.appointment_time.strftime('%H:%M') if a.appointment_time else None,
        'patient': a.patient.get_full_name() if a.patient else None,
        'doctor': a.doctor.get_full_name() if a.doctor else None,
        'status': a.status,
    } for a in appointments]
    return JsonResponse({'upcoming': data})


class AppointmentListView(SecureViewMixin, PatientAccessMixin, ListView):
    """List appointments with filtering and search - SECURE"""
    model = Appointment
    template_name = 'appointments/appointment_list.html'
    context_object_name = 'appointments'
    paginate_by = 20
    required_roles = ['admin', 'doctor', 'nurse', 'receptionist']
    
    def get_queryset(self):
        queryset = Appointment.objects.all().select_related('patient', 'doctor', 'created_by')
        
        # Apply filters from search form
        form = AppointmentSearchForm(data=self.request.GET)
        if form.is_valid():
            search = form.cleaned_data.get('search')
            if search:
                queryset = queryset.filter(
                    Q(patient__first_name__icontains=search) |
                    Q(patient__last_name__icontains=search) |
                    Q(doctor__first_name__icontains=search) |
                    Q(doctor__last_name__icontains=search) |
                    Q(appointment_number__icontains=search)
                )
            
            status = form.cleaned_data.get('status')
            if status:
                queryset = queryset.filter(status=status)
            
            priority = form.cleaned_data.get('priority')
            if priority:
                queryset = queryset.filter(priority=priority)
            
            date_from = form.cleaned_data.get('date_from')
            if date_from:
                queryset = queryset.filter(appointment_date__gte=date_from)
            
            date_to = form.cleaned_data.get('date_to')
            if date_to:
                queryset = queryset.filter(appointment_date__lte=date_to)
            
            doctor = form.cleaned_data.get('doctor')
            if doctor:
                queryset = queryset.filter(doctor=doctor)
        
        # Filter appointments by doctor if user is a doctor
        if self.request.user.is_authenticated and hasattr(self.request.user, 'role') and self.request.user.role == 'DOCTOR':
            try:
                doctor_instance = Doctor.objects.get(user=self.request.user)
                queryset = queryset.filter(doctor=doctor_instance)
                logger.info(f"DOCTOR {self.request.user.username} viewing only their appointments (Doctor ID: {doctor_instance.id})")
            except Doctor.DoesNotExist:
                logger.warning(f"Doctor instance not found for user {self.request.user.username}")
                queryset = queryset.none()
        
        return queryset.order_by('appointment_date', 'appointment_time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['search_form'] = AppointmentSearchForm(data=self.request.GET)

        # Statistics
        appointment_queryset = self.model.objects.all()
        today = timezone.now().date()

        # Total appointments count
        context['total_appointments'] = appointment_queryset.count()

        # Appointments by status
        context['scheduled_appointments'] = appointment_queryset.filter(
            status='SCHEDULED'
        ).count()

        context['pending_appointments'] = appointment_queryset.filter(
            status='PENDING'
        ).count()

        context['cancelled_appointments'] = appointment_queryset.filter(
            status='CANCELLED'
        ).count()

        # Today's appointments count
        context['today_appointments'] = appointment_queryset.filter(
            appointment_date=today
        ).count()

        context['completed_today'] = appointment_queryset.filter(
            appointment_date=today,
            status='COMPLETED'
        ).count()

        # Get all active doctors for filter dropdown
        # Try to respect tenant/hospital routing similar to doctors module
        try:
            hospital = getattr(self.request, 'hospital', None) or getattr(self.request.user, 'hospital', None)# 
            # hospital_db variable removed for unified single-DB mode
            context['doctors'] = Doctor.objects.filter(is_active=True).order_by('user__first_name')
        except Exception:
            # Fallback to default DB if tenant routing isn't available
            context['doctors'] = Doctor.objects.filter(is_active=True).order_by('user__first_name')

        # Get unique departments from appointments
        context['departments'] = appointment_queryset.values_list(
            'department', flat=True
        ).distinct().exclude(department__isnull=True).exclude(department='')

        # Add choices for filter dropdowns
        context['status_choices'] = self.model.STATUS_CHOICES
        context['priority_choices'] = self.model.PRIORITY_CHOICES

        # Add current filter values for form population
        context['search'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['priority_filter'] = self.request.GET.get('priority', '')
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')

        return context


class AppointmentDetailView(LoginRequiredMixin, DetailView):
    """Detailed appointment view"""
    model = Appointment
    template_name = 'appointments/appointment_detail.html'
    context_object_name = 'appointment'
    
    def get_queryset(self):
        return Appointment.objects.select_related('patient', 'doctor', 'created_by')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['history'] = self.object.history.all()
        context['can_reschedule'] = self.object.can_be_rescheduled()
        context['can_cancel'] = self.object.can_be_cancelled()
        context['reschedule_form'] = RescheduleAppointmentForm(appointment=self.object)
        context['cancel_form'] = CancelAppointmentForm()
        return context


class AppointmentCreateView(SecureViewMixin, PatientAccessMixin, CreateView):
    """Create new appointment - SECURE"""
    model = Appointment
    form_class = AppointmentForm
    template_name = 'appointments/appointment_form.html'
    required_roles = ['admin', 'doctor', 'nurse', 'receptionist']
    
    def get_initial(self):
        """Pre-populate form with patient from URL parameter"""
        initial = super().get_initial()
        patient_id = self.request.GET.get('patient')
        if patient_id:
            try:
                patient = Patient.objects.get(pk=patient_id)
                initial['patient'] = patient
            except Patient.DoesNotExist:
                pass
        return initial
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        
        # Set default appointment type if not specified
        if not form.instance.appointment_type:
            default_type = AppointmentType.objects.filter(
                name='General Consultation'
            ).first()
            if default_type:
                form.instance.appointment_type = default_type
        
        messages.success(self.request, 'Appointment scheduled successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('appointments:appointment_detail', kwargs={'pk': self.object.pk})


class AppointmentUpdateView(LoginRequiredMixin, UpdateView):
    """Update appointment"""
    model = Appointment
    form_class = AppointmentForm
    template_name = 'appointments/appointment_form.html'
    
    def get_queryset(self):
        return Appointment.objects.all()
    
    def form_valid(self, form):
        # Track status change
        if 'status' in form.changed_data:
            AppointmentHistory.objects.create(
                appointment=self.object,
                old_status=self.object.status,
                new_status=form.instance.status,
                changed_by=self.request.user
            )
        
        messages.success(self.request, 'Appointment updated successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('appointments:detail', kwargs={'pk': self.object.pk})


@login_required
def quick_appointment_create(request):
    """Quick appointment creation via HTMX"""
    if request.method == 'POST':
        form = QuickAppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.created_by = request.user
            
            # Set default values
            appointment.duration_minutes = 30
            appointment.priority = 'NORMAL'
            appointment.status = 'SCHEDULED'
            
            try:
                appointment.save()
                
                if request.headers.get('HX-Request'):
                    return JsonResponse({
                        'success': True,
                        'message': 'Appointment scheduled successfully!',
                        'appointment_id': str(appointment.id),
                        'redirect_url': reverse('appointments:detail', kwargs={'pk': appointment.pk})
                    })
                else:
                    messages.success(request, 'Appointment scheduled successfully!')
                    return redirect('appointments:detail', pk=appointment.pk)
                    
            except ValidationError as e:
                form.add_error(None, str(e))
    else:
        form = QuickAppointmentForm()
    
    return render(request, 'appointments/quick_create.html', {'form': form})


@login_required
def check_doctor_availability(request):
    """Check doctor availability for a specific date and time"""
    doctor_id = request.GET.get('doctor_id')
    date = request.GET.get('date')
    time = request.GET.get('time')
    appointment_id = request.GET.get('appointment_id')  # For updates
    
    if not all([doctor_id, date, time]):
        return JsonResponse({'available': False, 'message': 'Missing parameters'})
    
    try:
        doctor = Doctor.objects.get(id=doctor_id)
        appointment_date = datetime.strptime(date, '%Y-%m-%d').date()
        appointment_time = datetime.strptime(time, '%H:%M').time()
        
        # Check for conflicts
        conflicts = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            status__in=['SCHEDULED', 'CONFIRMED', 'CHECKED_IN', 'IN_PROGRESS']
        )
        
        if appointment_id:
            conflicts = conflicts.exclude(id=appointment_id)
        
        if conflicts.exists():
            return JsonResponse({
                'available': False,
                'message': 'Doctor is not available at this time'
            })
        
        return JsonResponse({'available': True, 'message': 'Doctor is available'})
        
    except (Doctor.DoesNotExist, ValueError):
        return JsonResponse({'available': False, 'message': 'Invalid data'})


@login_required
def reschedule_appointment(request, pk):
    """Reschedule an appointment"""
    appointment = get_object_or_404(Appointment, id=pk)
    
    if not appointment.can_be_rescheduled():
        messages.error(request, 'This appointment cannot be rescheduled.')
        return redirect('appointments:detail', pk=pk)
    
    if request.method == 'POST':
        form = RescheduleAppointmentForm(request.POST, appointment=appointment)
        if form.is_valid():
            # Update appointment
            old_date = appointment.appointment_date
            old_time = appointment.appointment_time
            
            appointment.appointment_date = form.cleaned_data['new_date']
            appointment.appointment_time = form.cleaned_data['new_time']
            appointment.status = 'RESCHEDULED'
            appointment.save()
            
            # Create history record
            AppointmentHistory.objects.create(
                appointment=appointment,
                old_status='SCHEDULED',
                new_status='RESCHEDULED',
                changed_by=request.user,
                reason=f"Rescheduled from {old_date} {old_time} to {appointment.appointment_date} {appointment.appointment_time}. Reason: {form.cleaned_data['reason']}"
            )
            
            messages.success(request, 'Appointment rescheduled successfully!')
            return redirect('appointments:detail', pk=pk)
    else:
        form = RescheduleAppointmentForm(appointment=appointment)
    
    return render(request, 'appointments/reschedule.html', {
        'appointment': appointment,
        'form': form
    })


@login_required
def cancel_appointment(request, pk):
    """Cancel an appointment"""
    appointment = get_object_or_404(Appointment, id=pk)
    
    if not appointment.can_be_cancelled():
        messages.error(request, 'This appointment cannot be cancelled.')
        return redirect('appointments:detail', pk=pk)
    
    if request.method == 'POST':
        form = CancelAppointmentForm(request.POST)
        if form.is_valid():
            # Update appointment
            old_status = appointment.status
            appointment.status = 'CANCELLED'
            appointment.cancelled_at = timezone.now()
            appointment.cancelled_by = request.user
            appointment.cancellation_reason = form.cleaned_data['reason']
            appointment.save()
            
            # Create history record
            AppointmentHistory.objects.create(
                appointment=appointment,
                old_status=old_status,
                new_status='CANCELLED',
                changed_by=request.user,
                reason=form.cleaned_data['reason']
            )
            
            # TODO: Send notification to patient if requested
            if form.cleaned_data.get('notify_patient'):
                pass  # Implement notification logic
            
            messages.success(request, 'Appointment cancelled successfully!')
            return redirect('appointments:list')
    else:
        form = CancelAppointmentForm()
    
    return render(request, 'appointments/cancel.html', {
        'appointment': appointment,
        'form': form
    })


@login_required
def check_in_appointment(request, pk):
    """Check in a patient for their appointment"""
    appointment = get_object_or_404(
        Appointment,
        id=pk,
        status__in=['SCHEDULED', 'CONFIRMED']
    )
    
    appointment.status = 'CHECKED_IN'
    appointment.checked_in_at = timezone.now()
    appointment.checked_in_by = request.user
    appointment.save()
    
    # Create history record
    AppointmentHistory.objects.create(
        appointment=appointment,
        old_status='SCHEDULED',
        new_status='CHECKED_IN',
        changed_by=request.user
    )
    
    messages.success(request, f'{appointment.patient.get_full_name()} has been checked in.')
    return redirect('appointments:detail', pk=pk)


@login_required
def complete_appointment(request, pk):
    """Mark appointment as completed"""
    appointment = get_object_or_404(
        Appointment,
        id=pk,
        status__in=['CHECKED_IN', 'IN_PROGRESS']
    )
    
    old_status = appointment.status
    appointment.status = 'COMPLETED'
    appointment.completed_at = timezone.now()
    appointment.save()
    
    # Update patient's last visit
    appointment.patient.last_visit = timezone.now()
    appointment.patient.save(update_fields=['last_visit'])
    
    # Create history record
    AppointmentHistory.objects.create(
        appointment=appointment,
        old_status=old_status,
        new_status='COMPLETED',
        changed_by=request.user
    )
    
    messages.success(request, 'Appointment marked as completed.')
    return redirect('appointments:detail', pk=pk)


@login_required
def appointment_calendar_view(request):
    """Calendar view of appointments"""
    today = timezone.now().date()
    
    # Get appointments for the current month
    appointments = Appointment.objects.filter(
        appointment_date__month=today.month,
        appointment_date__year=today.year
    ).select_related('patient', 'doctor')
    
    # Format appointments for calendar
    calendar_events = []
    for appointment in appointments:
        calendar_events.append({
            'id': str(appointment.id),
            'title': f"{appointment.patient.get_full_name()} - {appointment.doctor.get_full_name()}",
            'start': f"{appointment.appointment_date}T{appointment.appointment_time}",
            'end': appointment.get_end_datetime().isoformat(),
            'backgroundColor': appointment.appointment_type.color if appointment.appointment_type else '#007bff',
            'borderColor': appointment.appointment_type.color if appointment.appointment_type else '#007bff',
            'textColor': '#fff',
            'extendedProps': {
                'patient': appointment.patient.get_full_name(),
                'doctor': appointment.doctor.get_full_name(),
                'status': appointment.status,
                'chief_complaint': appointment.chief_complaint
            }
        })
    
    context = {
        'calendar_events': calendar_events,
        'doctors': Doctor.objects.filter(is_active=True)
    }
    
    return render(request, 'appointments/calendar.html', context)


@login_required
def appointment_list_enhanced(request):
    """Enhanced appointment list view with modern UI"""
    # Get search parameters
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    doctor_filter = request.GET.get('doctor', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Base queryset
    appointments = Appointment.objects.all().select_related('patient', 'doctor', 'created_by')
    doctors = Doctor.objects.filter(is_active=True)
    
    # Filter appointments by doctor if user is a doctor
    if request.user.is_authenticated and hasattr(request.user, 'role') and request.user.role == 'DOCTOR':
        try:
            doctor_instance = Doctor.objects.get(user=request.user)
            appointments = appointments.filter(doctor=doctor_instance)
            logger.info(f"DOCTOR {request.user.username} viewing only their appointments (Doctor ID: {doctor_instance.id})")
        except Doctor.DoesNotExist:
            logger.warning(f"Doctor instance not found for user {request.user.username}")
            appointments = Appointment.objects.none()
            messages.warning(request, 'Doctor profile not found. Please contact administrator.')
            return redirect('dashboard:home')
    
    # Apply filters
    if search:
        appointments = appointments.filter(
            Q(patient__first_name__icontains=search) |
            Q(patient__last_name__icontains=search) |
            Q(appointment_number__icontains=search)
        )
    
    if status_filter:
        appointments = appointments.filter(status=status_filter)
    
    if priority_filter:
        appointments = appointments.filter(priority=priority_filter)
    
    if doctor_filter:
        appointments = appointments.filter(doctor_id=doctor_filter)
    
    if date_from:
        appointments = appointments.filter(appointment_date__gte=date_from)
    
    if date_to:
        appointments = appointments.filter(appointment_date__lte=date_to)
    
    appointments = appointments.order_by('-appointment_date', '-appointment_time')
    
    # Get context data
    today = timezone.now().date()
    
    # Statistics
    stats = {
        'total': Appointment.objects.count(),
        'today': Appointment.objects.filter(appointment_date=today).count(),
        'scheduled': Appointment.objects.filter(status='SCHEDULED').count(),
        'completed': Appointment.objects.filter(status='COMPLETED').count(),
    }
    
    context = {
        'appointments': appointments,
        'doctors': doctors,
        'stats': stats,
        'search': search,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'doctor_filter': doctor_filter,
        'date_from': date_from,
        'date_to': date_to,
        'status_choices': Appointment.STATUS_CHOICES,
        'priority_choices': Appointment.PRIORITY_CHOICES,
    }
    
    return render(request, 'appointments/appointment_list.html', context)


@login_required
def appointment_create_enhanced(request):
    """Enhanced appointment creation view with wizard UI"""
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.created_by = request.user
            appointment.save()
            
            messages.success(request, 'Appointment scheduled successfully!')
            
            if request.headers.get('HX-Request'):
                return JsonResponse({
                    'success': True,
                    'message': 'Appointment scheduled successfully!',
                    'appointment_id': str(appointment.id),
                    'redirect_url': reverse('appointments:appointment_detail_enhanced', kwargs={'pk': appointment.pk})
                })
            
            return redirect('appointments:appointment_detail_enhanced', pk=appointment.pk)
    else:
        form = AppointmentForm()
        
        # Pre-populate with patient if provided
        patient_id = request.GET.get('patient')
        if patient_id:
            try:
                patient = Patient.objects.get(pk=patient_id, is_active=True)
                form.fields['patient'].initial = patient
            except Patient.DoesNotExist:
                pass
    
    context = {
        'form': form,
        'patients': Patient.objects.filter(is_active=True)[:50],
        'doctors': Doctor.objects.filter(is_active=True),
        'appointment_types': AppointmentType.objects.filter(is_active=True),
    }
    
    return render(request, 'appointments/appointment_create.html', context)


@login_required
def appointment_detail_enhanced(request, pk):
    """Enhanced appointment detail view with modern UI"""
    try:
        appointment = Appointment.objects.select_related('patient', 'doctor', 'created_by').get(pk=pk)
    except Appointment.DoesNotExist:
        # Render custom 404 page for better UX
        context = {
            'appointment_id': pk,
            'error_message': f'Appointment with ID {pk} does not exist or may have been deleted.'
        }
        return render(request, 'appointments/appointment_not_found.html', context, status=404)
    
    # Get related appointments for this patient
    related_appointments = Appointment.objects.filter(
        patient=appointment.patient).exclude(pk=appointment.pk).order_by('-appointment_date')[:5]
    
    # Get appointment history
    history = appointment.history.all().order_by('-created_at')
    
    context = {
        'appointment': appointment,
        'related_appointments': related_appointments,
        'history': history,
        'can_reschedule': appointment.can_be_rescheduled(),
        'can_cancel': appointment.can_be_cancelled(),
        'reschedule_form': RescheduleAppointmentForm(appointment=appointment),
        'cancel_form': CancelAppointmentForm(),
    }
    
    return render(request, 'appointments/appointment_detail.html', context)


@login_required
def appointment_calendar(request):
    """Enhanced calendar view"""
    # Get active doctors and appointment types
    doctors = Doctor.objects.filter(is_active=True)
    appointment_types = AppointmentType.objects.filter(is_active=True)
    
    # Get today's appointments for sidebar
    today = timezone.now().date()
    today_appointments = Appointment.objects.filter(
        appointment_date=today
    ).select_related('patient', 'doctor').order_by('appointment_time')
    
    # Calculate statistics
    this_month = today.replace(day=1)
    next_month = (this_month + timezone.timedelta(days=32)).replace(day=1)
    
    stats = {
        'total_this_month': Appointment.objects.filter(
            appointment_date__gte=this_month,
            appointment_date__lt=next_month
        ).count(),
        'today_count': today_appointments.count(),
        'this_week': Appointment.objects.filter(
            appointment_date__gte=today - timezone.timedelta(days=today.weekday()),
            appointment_date__lt=today + timezone.timedelta(days=7-today.weekday())
        ).count(),
        'active_doctors': doctors.count(),
    }
    
    context = {
        'doctors': doctors,
        'appointment_types': appointment_types,
        'today_appointments': today_appointments,
        'stats': stats,
    }
    
    return render(request, 'appointments/appointment_calendar.html', context)


@login_required
def calendar_events(request):
    """JSON endpoint for calendar events"""
    start = request.GET.get('start')
    end = request.GET.get('end')
    doctor_id = request.GET.get('doctor')
    
    appointments = Appointment.objects.all().select_related('patient', 'doctor')
    
    # Parse datetime strings to date objects for filtering
    if start:
        try:
            # Handle different datetime formats from FullCalendar
            if 'T' in start:
                # ISO format with time
                start_date = datetime.fromisoformat(start.replace('Z', '+00:00')).date()
            else:
                # Just date format
                start_date = datetime.strptime(start, '%Y-%m-%d').date()
            appointments = appointments.filter(appointment_date__gte=start_date)
        except (ValueError, TypeError):
            pass
            
    if end:
        try:
            # Handle different datetime formats from FullCalendar
            if 'T' in end:
                # ISO format with time
                end_date = datetime.fromisoformat(end.replace('Z', '+00:00')).date()
            else:
                # Just date format
                end_date = datetime.strptime(end, '%Y-%m-%d').date()
            appointments = appointments.filter(appointment_date__lte=end_date)
        except (ValueError, TypeError):
            pass
            
    if doctor_id and doctor_id != 'all':
        try:
            appointments = appointments.filter(doctor_id=int(doctor_id))
        except (ValueError, TypeError):
            pass
    
    events = []
    for appointment in appointments:
        color = '#28a745'  # Default green
        if appointment.status == 'CANCELLED':
            color = '#dc3545'  # Red
        elif appointment.status == 'COMPLETED':
            color = '#6c757d'  # Gray
        elif appointment.status == 'IN_PROGRESS':
            color = '#007bff'  # Blue
        elif appointment.priority == 'HIGH':
            color = '#fd7e14'  # Orange
        elif appointment.priority == 'URGENT':
            color = '#dc3545'  # Red
        
        events.append({
            'id': str(appointment.id),
            'title': f"{appointment.patient.get_full_name()}",
            'start': f"{appointment.appointment_date}T{appointment.appointment_time}",
            'end': appointment.get_end_datetime().isoformat() if hasattr(appointment, 'get_end_datetime') else None,
            'backgroundColor': color,
            'borderColor': color,
            'textColor': '#fff',
            'extendedProps': {
                'patient': appointment.patient.get_full_name(),
                'doctor': appointment.doctor.get_full_name(),
                'status': appointment.status,
                'priority': appointment.priority,
                'chief_complaint': appointment.chief_complaint or '',
                'phone': appointment.patient.phone or '',
            }
        })
    
    return JsonResponse(events, safe=False)


@login_required
def today_appointments_widget(request):
    """Widget showing today's appointments"""
    today = timezone.now().date()
    appointments = Appointment.objects.filter(
        appointment_date=today
    ).select_related('patient', 'doctor').order_by('appointment_time')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        appointments = appointments.filter(status=status_filter)
    
    context = {
        'appointments': appointments,
        'today': today,
    }
    
    return render(request, 'appointments/today_appointments.html', context)


@login_required
def upcoming_appointments_list(request):
    """AJAX endpoint for upcoming appointments"""
    limit = int(request.GET.get('limit', 10))
    appointments = Appointment.objects.filter(
        appointment_date__gte=timezone.now().date()
    ).select_related('patient', 'doctor').order_by('appointment_date', 'appointment_time')[:limit]
    
    data = [{
        'id': str(a.id),
        'patient_name': a.patient.get_full_name(),
        'doctor_name': a.doctor.get_full_name(),
        'date': a.appointment_date.strftime('%Y-%m-%d'),
        'time': a.appointment_time.strftime('%H:%M'),
        'status': a.status,
        'priority': a.priority,
        'url': reverse('appointments:appointment_detail_enhanced', kwargs={'pk': a.pk})
    } for a in appointments]
    
    return JsonResponse({'appointments': data})


@login_required
def get_available_time_slots(request):
    """Enhanced time slots endpoint using actual doctor schedules"""
    doctor_id = request.GET.get('doctor_id')
    date = request.GET.get('date')
    exclude_id = request.GET.get('exclude')
    
    if not doctor_id or not date:
        return JsonResponse({'slots': [], 'error': 'Missing doctor_id or date'})
    
    try:
        doctor = Doctor.objects.get(id=doctor_id)
        appointment_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Get doctor's schedule for this day
        day_of_week = appointment_date.weekday()  # 0 = Monday
        schedules = DoctorSchedule.objects.filter(
            doctor=doctor,
            day_of_week=day_of_week,
            is_active=True
        )
        
        if not schedules.exists():
            return JsonResponse({'slots': [], 'error': f'No schedules found for day {day_of_week}'})
        
        # Generate time slots based on actual schedules
        slots = []
        
        for schedule in schedules:
            start_hour = schedule.start_time.hour
            start_minute = schedule.start_time.minute
            end_hour = schedule.end_time.hour
            end_minute = schedule.end_time.minute
            interval = 30  # 30 minutes
            
            # Get existing appointments for this doctor and date
            existing_qs = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=appointment_date,
                status__in=['SCHEDULED', 'CONFIRMED', 'CHECKED_IN', 'IN_PROGRESS']
            )
            if exclude_id:
                try:
                    existing_qs = existing_qs.exclude(id=exclude_id)
                except Exception:
                    pass
            existing_times = [t.strftime('%H:%M') for t in existing_qs.values_list('appointment_time', flat=True) if t]
            
            # Generate slots for this schedule
            current_hour = start_hour
            current_minute = start_minute
            
            while (current_hour < end_hour) or (current_hour == end_hour and current_minute < end_minute):
                # Skip break time if defined
                time_obj = datetime.strptime(f"{current_hour:02d}:{current_minute:02d}", '%H:%M').time()
                
                if schedule.break_start_time and schedule.break_end_time:
                    if schedule.break_start_time <= time_obj <= schedule.break_end_time:
                        # Skip this slot - it's break time
                        current_minute += interval
                        if current_minute >= 60:
                            current_minute = 0
                            current_hour += 1
                        continue
                slot_time_str = f"{current_hour:02d}:{current_minute:02d}"
                available = slot_time_str not in existing_times
                slots.append({'time': slot_time_str, 'available': available})
                
                # Advance by interval
                current_minute += interval
                if current_minute >= 60:
                    current_minute = 0
                    current_hour += 1
        
        # Deduplicate times across multiple schedules, keep available=True if any schedule has it available
        dedup = {}
        for s in slots:
            t = s['time']
            if t not in dedup:
                dedup[t] = s['available']
            else:
                dedup[t] = dedup[t] or s['available']
        final_slots = [{'time': t, 'available': dedup[t]} for t in sorted(dedup.keys())]
        
        return JsonResponse({'slots': final_slots})
    except Doctor.DoesNotExist:
        return JsonResponse({'slots': [], 'error': 'Doctor not found'})
    except Exception as e:
        logger.exception(f"Error getting available time slots: {e}")
        return JsonResponse({'slots': [], 'error': 'Internal server error'})


@login_required
def start_consultation(request, pk):
    """Start consultation for an appointment"""
    appointment = get_object_or_404(
        Appointment,
        pk=pk,
        status='CHECKED_IN'
    )
    
    appointment.status = 'IN_PROGRESS'
    appointment.consultation_started_at = timezone.now()
    appointment.save()
    
    # Create history record
    AppointmentHistory.objects.create(
        appointment=appointment,
        old_status='CHECKED_IN',
        new_status='IN_PROGRESS',
        changed_by=request.user
    )
    
    messages.success(request, 'Consultation started.')
    return redirect('appointments:appointment_detail_enhanced', pk=pk)


@login_required
def send_reminder(request, pk):
    """Send reminder for appointment"""
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # TODO: Implement SMS/Email reminder logic
    messages.success(request, f'Reminder sent to {appointment.patient.get_full_name()}')
    return redirect('appointments:appointment_detail_enhanced', pk=pk)


@login_required
def export_appointments(request):
    """Export appointments to CSV"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="appointments.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Appointment Number', 'Patient', 'Doctor', 'Date', 'Time', 
        'Status', 'Priority', 'Chief Complaint', 'Created At'
    ])
    
    appointments = Appointment.objects.all().select_related('patient', 'doctor').order_by('-appointment_date')
    
    for appointment in appointments:
        writer.writerow([
            appointment.appointment_number,
            appointment.patient.get_full_name(),
            appointment.doctor.get_full_name(),
            appointment.appointment_date,
            appointment.appointment_time,
            appointment.status,
            appointment.priority,
            appointment.chief_complaint or '',
            appointment.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    return response


@login_required
def print_appointment(request, pk):
    """Redirect legacy print to enhanced print view for a single, modern template."""
    return redirect('appointments:appointment_print', appointment_id=pk)


@login_required
def export_appointment_pdf(request, pk):
    """Export single appointment to PDF"""
    # Redirect to print view for now
    return redirect('appointments:appointment_print', appointment_id=pk)


@login_required
def bulk_appointment_action(request):
    """Handle bulk appointment actions"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    action = request.POST.get('action')
    appointment_ids = request.POST.getlist('appointments[]')
    
    if not appointment_ids:
        return JsonResponse({'success': False, 'error': 'No appointments selected'})
    
    try:
        appointments = Appointment.objects.filter(id__in=appointment_ids)
        updated_count = 0
        
        if action == 'update-status':
            status = request.POST.get('status')
            if status in [choice[0] for choice in Appointment.STATUS_CHOICES]:
                updated_count = appointments.update(status=status)
                
        elif action == 'send-reminders':
            # TODO: Implement reminder sending logic
            updated_count = len(appointment_ids)
            
        elif action == 'cancel':
            reason = request.POST.get('reason', 'Bulk cancellation')
            updated_count = appointments.update(
                status='CANCELLED',
                cancelled_at=timezone.now(),
                cancelled_by=request.user,
                cancellation_reason=reason
            )
        
        return JsonResponse({
            'success': True, 
            'message': f'Successfully processed {updated_count} appointment(s)'
        })
        
    except Exception as e:
        logger.error(f"Bulk action error: {e}")
        return JsonResponse({'success': False, 'error': 'An error occurred processing the request'})


@login_required
def communication_status_api(request):
    """API endpoint to get communication status for appointments"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        import json
        data = json.loads(request.body)
        appointment_ids = data.get('appointment_ids', [])
        
        if not appointment_ids:
            return JsonResponse({'error': 'No appointment IDs provided'}, status=400)
        
        from apps.communications.models import CommunicationLog
        from apps.communications.templatetags.communication_tags import communication_status
        
        appointments = Appointment.objects.filter(id__in=appointment_ids)
        
        result = {}
        channels = ['whatsapp', 'telegram', 'viber', 'email']
        
        for appointment in appointments:
            appointment_statuses = {}
            for channel in channels:
                status_info = communication_status(appointment, channel)
                appointment_statuses[channel] = status_info
            
            result[str(appointment.id)] = appointment_statuses
        
        return JsonResponse({
            'success': True,
            'communications': result
        })
        
    except Exception as e:
        logger.error(f"Communication status API error: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


# ========================================
# EXTENDED APPOINTMENT FUNCTIONALITY
# ========================================

@require_http_methods(["GET"])
def get_patient_previous_appointments(request, patient_id):
    """Get previous appointments for a patient for follow-up selection"""
    try:
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Patient not found'
            }, status=404)
        
        # Get completed appointments for this patient
        appointments = Appointment.objects.filter(
            patient=patient,
            status__in=['COMPLETED', 'NO_SHOW']
        ).select_related('doctor').order_by('-appointment_date', '-appointment_time')[:10]
        
        appointment_list = []
        for appointment in appointments:
            appointment_list.append({
                'id': str(appointment.id),
                'appointment_number': appointment.appointment_number,
                'date': appointment.appointment_date.strftime('%Y-%m-%d'),
                'time': appointment.appointment_time.strftime('%H:%M'),
                'doctor': appointment.doctor.get_full_name(),
                'department': appointment.department,
                'chief_complaint': appointment.chief_complaint[:50] + '...' if len(appointment.chief_complaint) > 50 else appointment.chief_complaint,
                'display_text': f"{appointment.appointment_number} - {appointment.appointment_date.strftime('%d/%m/%Y')} - Dr. {appointment.doctor.get_full_name()}"
            })
        
        return JsonResponse({
            'success': True,
            'appointments': appointment_list
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required
def appointment_create_super_enhanced(request):
    """Enhanced appointment creation with calendar and notifications"""
    if request.method == 'GET':
        try:
            tz_name = timezone.get_current_timezone_name()
        except Exception:
            tz_name = str(timezone.get_current_timezone())
        tz_abbrev = timezone.localtime(timezone.now()).strftime('%Z')
        context = {
            'active_timezone': tz_name,
            'active_timezone_abbrev': tz_abbrev,
        }
        return render(request, 'appointments/appointment_create_super.html', context)
    
    elif request.method == 'POST':
        return create_enhanced_appointment(request)


@csrf_exempt
def create_enhanced_appointment(request):
    """Create appointment with notifications and serial number generation"""
    try:
        with transaction.atomic():
            # Get form data
            patient_id = request.POST.get('patient_id')
            doctor_id = request.POST.get('doctor_id')
            department = request.POST.get('department')
            appointment_date = request.POST.get('appointment_date')
            appointment_time = request.POST.get('appointment_time')
            slot_time_start = request.POST.get('slot_time_start')
            slot_time_end = request.POST.get('slot_time_end')
            chief_complaint = request.POST.get('chief_complaint')
            symptoms = request.POST.get('symptoms', '')
            notes = request.POST.get('notes', '')
            priority = request.POST.get('priority', 'NORMAL')
            consultation_fee = request.POST.get('consultation_fee', '0.00')
            patient_phone = request.POST.get('patient_phone', '')
            patient_email = request.POST.get('patient_email', '')
            
            # Enhanced fields
            appointment_type = request.POST.get('appointment_type', 'CONSULTATION')
            duration_minutes = request.POST.get('duration_minutes', '30')
            is_follow_up = request.POST.get('is_follow_up') == 'on'
            status = request.POST.get('status', 'SCHEDULED')
            previous_appointment_id = request.POST.get('previous_appointment')
            
            # Notification settings
            notification_types = []
            if request.POST.get('notification_email'):
                notification_types.append('EMAIL')
            if request.POST.get('notification_whatsapp'):
                notification_types.append('WHATSAPP')
            if request.POST.get('notification_telegram'):
                notification_types.append('TELEGRAM')
            if request.POST.get('notification_viber'):
                notification_types.append('VIBER')
            
            # Validate required fields
            if not all([patient_id, doctor_id, appointment_date, appointment_time, chief_complaint]):
                return JsonResponse({
                    'success': False, 
                    'message': 'Missing required fields'
                })
            
            try:
                patient = Patient.objects.get(id=patient_id)
                doctor = Doctor.objects.get(id=doctor_id)
            except (Patient.DoesNotExist, Doctor.DoesNotExist):
                return JsonResponse({'success': False, 'message': 'Invalid patient or doctor'}, status=400)
            
            # Parse date and time
            date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
            time_obj = datetime.strptime(appointment_time, '%H:%M').time()
            
            if not slot_time_start or not slot_time_end:
                return JsonResponse({
                    'success': False,
                    'message': 'Please select a time slot before creating the appointment.'
                }, status=400)
            
            slot_start_time = datetime.strptime(slot_time_start, '%H:%M').time()
            slot_end_time = datetime.strptime(slot_time_end, '%H:%M').time()
            
            # Validate time falls within slot
            if not (slot_start_time <= time_obj < slot_end_time):
                return JsonResponse({
                    'success': False,
                    'message': 'Selected time is outside of the chosen slot window.'
                }, status=400)
            
            # Check availability
            day_of_week = date_obj.weekday()
            schedule_qs = DoctorSchedule.objects.filter(
                doctor=doctor,
                day_of_week=day_of_week,
                is_active=True,
            )
            
            schedule = schedule_qs.filter(start_time=slot_start_time, end_time=slot_end_time).first()
            if not schedule:
                schedule = schedule_qs.filter(start_time__lte=slot_start_time, end_time__gte=slot_end_time).first()
            if not schedule:
                return JsonResponse({
                    'success': False,
                    'message': 'No active schedule for this window.'
                }, status=400)
            
            capacity = (schedule.max_patients if getattr(schedule, 'max_patients', None) else 1)
            
            booked_count = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=date_obj,
                appointment_time__gte=slot_start_time,
                appointment_time__lt=slot_end_time,
                status__in=['SCHEDULED', 'CONFIRMED', 'CHECKED_IN', 'IN_PROGRESS']
            ).count()
            
            if booked_count >= capacity:
                return JsonResponse({
                    'success': False,
                    'message': 'Selected slot is full. Please pick another slot.'
                }, status=400)
            
            # Handle previous appointment for follow-ups
            previous_appointment = None
            if is_follow_up and previous_appointment_id:
                try:
                    previous_appointment = Appointment.objects.get(id=previous_appointment_id)
                except Appointment.DoesNotExist:
                    previous_appointment = None
            
            # Create appointment
            appointment = Appointment.objects.create(
                patient=patient,
                doctor=doctor,
                department=department,
                appointment_date=date_obj,
                appointment_time=time_obj,
                slot_time_start=slot_start_time,
                slot_time_end=slot_end_time,
                chief_complaint=chief_complaint,
                symptoms=symptoms,
                notes=notes,
                priority=priority,
                consultation_fee=float(consultation_fee) if consultation_fee else 0.00,
                patient_phone=patient_phone,
                patient_email=patient_email,
                created_by=request.user,
                status=status,
                is_follow_up=is_follow_up,
                previous_appointment=previous_appointment
            )
            
            # Send notifications
            notification_warning = None
            if notification_types:
                try:
                    send_appointment_notifications(appointment, notification_types)
                except Exception as notify_err:
                    notification_warning = str(notify_err)
            
            return JsonResponse({
                'success': True,
                'message': 'Appointment created successfully',
                'appointment': {
                    'id': str(appointment.id),
                    'appointment_number': appointment.appointment_number,
                    'serial_number': appointment.serial_number,
                    'barcode': appointment.barcode,
                    'patient_name': appointment.patient.get_full_name(),
                    'doctor_name': appointment.doctor.get_full_name(),
                    'date': appointment.appointment_date.strftime('%Y-%m-%d'),
                    'time': appointment.appointment_time.strftime('%H:%M'),
                    'department': appointment.department,
                },
                **({'notification_warning': notification_warning} if notification_warning else {})
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


def send_appointment_notifications(appointment, notification_types):
    """Send appointment notifications via various channels"""
    try:
        message = f"""
Appointment Confirmation

Dear {appointment.patient.get_full_name()},

Your appointment has been scheduled:

📅 Date: {appointment.appointment_date.strftime('%B %d, %Y')}
🕒 Time: {appointment.appointment_time.strftime('%I:%M %p')}
👨‍⚕️ Doctor: Dr. {appointment.doctor.get_full_name()}
🏥 Department: {appointment.department}
🎫 Serial Number: {appointment.serial_number}
📋 Appointment Number: {appointment.appointment_number}

Please arrive 15 minutes before your appointment time.

Thank you!
        """
        
        for notification_type in notification_types:
            if notification_type == 'EMAIL' and appointment.patient_email:
                send_email_notification(appointment, message)
            elif notification_type == 'WHATSAPP' and appointment.patient_phone:
                send_whatsapp_notification(appointment, message)
            elif notification_type == 'TELEGRAM' and appointment.patient_phone:
                send_telegram_notification(appointment, message)
            elif notification_type == 'VIBER' and appointment.patient_phone:
                send_viber_notification(appointment, message)
        
        # Mark as sent
        appointment.notification_sent = True
        appointment.save(update_fields=['notification_sent'])
        
    except Exception as e:
        print(f"Error sending notifications: {e}")


def send_email_notification(appointment, message):
    """Send email notification"""
    from django.core.mail import send_mail
    from django.conf import settings
    
    try:

        send_mail(
            subject=f'Appointment Confirmation - {appointment.appointment_number}',
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[appointment.patient_email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Email notification error: {e}")


def send_whatsapp_notification(appointment, message):
    """Send WhatsApp notification (implement with WhatsApp Business API)"""
    print(f"WhatsApp notification would be sent to {appointment.patient_phone}: {message}")


def send_telegram_notification(appointment, message):
    """Send Telegram notification"""
    print(f"Telegram notification would be sent to {appointment.patient_phone}: {message}")


def send_viber_notification(appointment, message):
    """Send Viber notification"""
    print(f"Viber notification would be sent to {appointment.patient_phone}: {message}")


def get_department_icon(department):
    """Get Bootstrap icon for department"""
    icons = {
        'GENERAL_MEDICINE': 'heart-pulse',
        'CARDIOLOGY': 'heart',
        'NEUROLOGY': 'brain',
        'ORTHOPEDICS': 'bandaid',
        'PEDIATRICS': 'emoji-smile',
        'GYNECOLOGY': 'gender-female',
        'DERMATOLOGY': 'droplet',
        'PSYCHIATRY': 'chat-heart',
        'OPHTHALMOLOGY': 'eye',
        'OTOLARYNGOLOGY': 'mic',
        'GENERAL_SURGERY': 'scissors',
        'ANESTHESIOLOGY': 'heart-pulse-fill',
        'RADIOLOGY': 'radioactive',
        'PATHOLOGY': 'microscope',
        'EMERGENCY_MEDICINE': 'hospital',
        'INTERNAL_MEDICINE': 'activity',
        'FAMILY_MEDICINE': 'people',
        'GASTROENTEROLOGY': 'diagram-3',
        'ENDOCRINOLOGY': 'droplet-half',
        'NEPHROLOGY': 'droplet',
        'ONCOLOGY': 'shield-check',
        'HEMATOLOGY': 'droplet-fill',
        'RHEUMATOLOGY': 'activity',
        'UROLOGY': 'droplet',
        'PLASTIC_SURGERY': 'bandaid-fill',
        'NEUROSURGERY': 'brain',
        'CARDIOTHORACIC_SURGERY': 'heart-pulse',
        'PULMONOLOGY': 'lungs',
        'INFECTIOUS_DISEASE': 'virus',
        'GERIATRICS': 'person-walking',
        'OBSTETRICS': 'person-heart',
    }
    return icons.get(department, 'hospital')


def get_department_description(department):
    """Get description for department"""
    descriptions = {
        'GENERAL_MEDICINE': 'General medical care and consultations',
        'CARDIOLOGY': 'Heart and cardiovascular system care',
        'NEUROLOGY': 'Brain, spine and nervous system disorders',
        'ORTHOPEDICS': 'Bone, joint and muscle treatment',
        'PEDIATRICS': 'Medical care for infants, children and adolescents',
        'GYNECOLOGY': 'Women\'s reproductive health',
        'DERMATOLOGY': 'Skin, hair and nail conditions',
        'PSYCHIATRY': 'Mental health and behavioral disorders',
        'OPHTHALMOLOGY': 'Eye and vision care',
        'OTOLARYNGOLOGY': 'Ear, nose and throat treatment',
        'GENERAL_SURGERY': 'Surgical procedures and operations',
        'ANESTHESIOLOGY': 'Anesthesia and pain management',
        'RADIOLOGY': 'Medical imaging and diagnostics',
        'PATHOLOGY': 'Laboratory diagnosis of diseases',
        'EMERGENCY_MEDICINE': 'Urgent and emergency medical care',
        'INTERNAL_MEDICINE': 'Adult internal organ disorders',
        'FAMILY_MEDICINE': 'Comprehensive family healthcare',
        'GASTROENTEROLOGY': 'Digestive system disorders',
        'ENDOCRINOLOGY': 'Hormone and metabolic disorders',
        'NEPHROLOGY': 'Kidney and urinary system care',
        'ONCOLOGY': 'Cancer diagnosis and treatment',
        'HEMATOLOGY': 'Blood disorders and diseases',
        'RHEUMATOLOGY': 'Joint, muscle and autoimmune disorders',
        'UROLOGY': 'Urinary tract and male reproductive system',
        'PLASTIC_SURGERY': 'Reconstructive and cosmetic surgery',
        'NEUROSURGERY': 'Surgical treatment of brain and spine',
        'CARDIOTHORACIC_SURGERY': 'Heart and chest surgery',
        'PULMONOLOGY': 'Lung and respiratory system care',
        'INFECTIOUS_DISEASE': 'Infectious and communicable diseases',
        'GERIATRICS': 'Healthcare for elderly patients',
        'OBSTETRICS': 'Pregnancy, childbirth and maternal care',
    }
    return descriptions.get(department, 'Specialized medical care')


# Missing view functions for enhanced appointments
def get_departments(request):
    """Get all departments for appointments"""
    try:
        from apps.departments.models import Department
        departments = Department.objects.filter(is_active=True).values('id', 'name', 'code')
        return JsonResponse({
            'departments': list(departments),
            'success': True
        })
    except ImportError:
        # Fallback if no departments app
        return JsonResponse({
            'departments': [
                {'id': 1, 'name': 'General Medicine', 'code': 'GM'},
                {'id': 2, 'name': 'Cardiology', 'code': 'CARD'},
                {'id': 3, 'name': 'Orthopedics', 'code': 'ORTH'},
                {'id': 4, 'name': 'Pediatrics', 'code': 'PED'},
            ],
            'success': True
        })


def get_doctors_by_department(request, department_id):
    """Get doctors by department"""
    try:
        doctors = Doctor.objects.filter(
            department_id=department_id,
            is_active=True
        ).select_related('user').values(
            'id', 'user__first_name', 'user__last_name', 
            'specialization', 'consultation_fee'
        )
        return JsonResponse({
            'doctors': list(doctors),
            'success': True
        })
    except Exception as e:
        return JsonResponse({
            'doctors': [],
            'success': False,
            'error': str(e)
        })


def get_enhanced_time_slots(request):
    """Get available time slots for appointments"""
    doctor_id = request.GET.get('doctor_id')
    date = request.GET.get('date')
    
    if not doctor_id or not date:
        return JsonResponse({
            'time_slots': [],
            'success': False,
            'error': 'Doctor ID and date are required'
        })
    
    try:
        # Generate time slots (9 AM to 6 PM)
        time_slots = []
        from datetime import datetime, time
        start_time = time(9, 0)  # 9:00 AM
        end_time = time(18, 0)   # 6:00 PM
        
        current_time = datetime.combine(datetime.strptime(date, '%Y-%m-%d').date(), start_time)
        end_datetime = datetime.combine(datetime.strptime(date, '%Y-%m-%d').date(), end_time)
        
        while current_time < end_datetime:
            time_str = current_time.strftime('%H:%M')
            
            # Check if slot is already booked
            is_booked = Appointment.objects.filter(
                doctor_id=doctor_id,
                appointment_date=date,
                appointment_time=current_time.time(),
                status__in=['scheduled', 'confirmed']
            ).exists()
            
            time_slots.append({
                'time': time_str,
                'available': not is_booked
            })
            
            # Add 30 minutes
            current_time = current_time.replace(minute=current_time.minute + 30)
            if current_time.minute == 60:
                current_time = current_time.replace(hour=current_time.hour + 1, minute=0)
        
        return JsonResponse({
            'time_slots': time_slots,
            'success': True
        })
    except Exception as e:
        return JsonResponse({
            'time_slots': [],
            'success': False,
            'error': str(e)
        })


def get_month_availability_days(request):
    """Get available days in a month for appointments"""
    doctor_id = request.GET.get('doctor_id')
    year = request.GET.get('year')
    month = request.GET.get('month')
    
    if not doctor_id or not year or not month:
        return JsonResponse({
            'available_days': [],
            'success': False,
            'error': 'Doctor ID, year, and month are required'
        })
    
    try:
        from datetime import datetime, timedelta
        import calendar
        
        year = int(year)
        month = int(month)
        
        # Get number of days in month
        num_days = calendar.monthrange(year, month)[1]
        available_days = []
        
        for day in range(1, num_days + 1):
            date = datetime(year, month, day).date()
            
            # Skip past dates
            if date < timezone.now().date():
                continue
                
            # Skip Sundays (assuming clinic is closed on Sundays)
            if date.weekday() == 6:  # Sunday is 6
                continue
            
            # Check if doctor has any availability
            appointments_count = Appointment.objects.filter(
                doctor_id=doctor_id,
                appointment_date=date,
                status__in=['scheduled', 'confirmed']
            ).count()
            
            # Assuming max 16 appointments per day (8 hours * 2 slots per hour)
            if appointments_count < 16:
                available_days.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'day': day,
                    'available_slots': 16 - appointments_count
                })
        
        return JsonResponse({
            'available_days': available_days,
            'success': True
        })
    except Exception as e:
        return JsonResponse({
            'available_days': [],
            'success': False,
            'error': str(e)
        })


def appointment_print(request, pk):
    """Print appointment details"""
    try:
        appointment = get_object_or_404(Appointment, pk=pk)
        context = {
            'appointment': appointment,
            'print_date': timezone.now(),
        }
        return render(request, 'appointments/print_appointment.html', context)
    except Exception as e:
        messages.error(request, f'Error printing appointment: {str(e)}')
        return redirect('appointments:appointment_list')


def generate_appointment_barcode(request, appointment_id):
    """Generate barcode for appointment"""
    try:
        appointment = get_object_or_404(Appointment, pk=appointment_id)
        
        # Create a simple barcode representation
        barcode_data = f"APT-{appointment.id}-{appointment.appointment_date.strftime('%Y%m%d')}"
        
        return JsonResponse({
            'barcode': barcode_data,
            'success': True,
            'appointment_id': str(appointment.id)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })