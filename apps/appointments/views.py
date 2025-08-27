# apps/appointments/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from .models import Appointment, AppointmentType, AppointmentHistory
from .forms import (
    AppointmentForm, QuickAppointmentForm, AppointmentSearchForm,
    RescheduleAppointmentForm, CancelAppointmentForm
)
from apps.patients.models import Patient
from apps.doctors.models import Doctor
# from tenants.permissions import  # Temporarily commented TenantFilterMixin
from apps.core.utils.qr_code import document_qr_generator
from apps.core.mixins import TenantSafeMixin, RequireHospitalSelectionMixin, require_hospital_selection

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


@require_hospital_selection
def get_doctors(request):
    """Return a small JSON list of doctors for the current hospital.

    Expected query params:
    - hospital_id (optional)
    - q (optional) search string
    """
    q = request.GET.get('q', '')
    # Use simple filtering by name/specialty; DB router ensures correct tenant
    doctors = Doctor.objects.filter(is_active=True)
    if q:
        doctors = doctors.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(specialization__icontains=q)
        )

    data = [{'id': str(d.id), 'name': d.get_full_name(), 'specialty': getattr(d, 'specialty', '')} for d in doctors[:50]]
    return JsonResponse({'results': data})


@require_hospital_selection
def search_patients(request):
    """Simple patient search endpoint used by some AJAX calls."""
    q = request.GET.get('q', '')
    patients = Patient.objects.all()
    if q:
        patients = patients.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(phone__icontains=q)
        )

    data = [{'id': p.id, 'text': p.get_full_name(), 'phone': p.phone} for p in patients[:50]]
    return JsonResponse({'results': data})


@require_hospital_selection
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


@require_hospital_selection
def upcoming_appointments(request):
    """Return a small list of upcoming appointments for the current user's hospital."""
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

class AppointmentListView(TenantSafeMixin, ListView):  # TenantFilterMixin temporarily commented:
    """List appointments with filtering and search"""
    model = Appointment
    template_name = 'appointments/appointment_list.html'
    context_object_name = 'appointments'
    paginate_by = 20
    required_roles = ['admin', 'doctor', 'nurse', 'receptionist']
    
    def get_queryset(self):
        # Tenant-safe queryset
        queryset = self.filter_by_tenant(Appointment.objects.all()).select_related('patient', 'doctor', 'created_by')
        
        # Apply filters from search form
        # Get tenant from session selected hospital code
        tenant_code = self.request.session.get('selected_hospital_code')
        form = AppointmentSearchForm(data=self.request.GET, hospital=tenant_code)
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
        
        return queryset.order_by('appointment_date', 'appointment_time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = AppointmentSearchForm(
            data=self.request.GET,
            tenant=self.get_current_tenant()
        )
        
        # Statistics - use tenant-safe queryset
        appointment_queryset = self.get_tenant_safe_queryset(Appointment)
        today = timezone.now().date()
        
        context['today_appointments'] = appointment_queryset.filter(
            appointment_date=today
        ).count()
        
        context['pending_appointments'] = appointment_queryset.filter(
            status='SCHEDULED'
        ).count()
        
        context['completed_today'] = appointment_queryset.filter(
            appointment_date=today,
            status='COMPLETED'
        ).count()
        
        # Add flag to indicate if no hospital is selected
        context['no_hospital_selected'] = self.get_current_tenant() is None
        
        return context


class AppointmentDetailView(LoginRequiredMixin, DetailView):
    """Detailed appointment view"""
    model = Appointment
    template_name = 'appointments/appointment_detail.html'
    context_object_name = 'appointment'
    
    def get_queryset(self):
        return Appointment.objects.filter(
            ).select_related('patient', 'doctor', 'created_by')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['history'] = self.object.history.all()
        context['can_reschedule'] = self.object.can_be_rescheduled()
        context['can_cancel'] = self.object.can_be_cancelled()
        context['reschedule_form'] = RescheduleAppointmentForm(appointment=self.object)
        context['cancel_form'] = CancelAppointmentForm()
        return context


class AppointmentCreateView(RequireHospitalSelectionMixin, CreateView):
    """Create new appointment"""
    model = Appointment
    form_class = AppointmentForm
    template_name = 'appointments/appointment_form.html'
    required_roles = ['admin', 'doctor', 'nurse', 'receptionist']
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['hospital'] = self.request.session.get('selected_hospital_code')
        return kwargs
    
    def get_initial(self):
        """Pre-populate form with patient from URL parameter"""
        initial = super().get_initial()
        patient_id = self.request.GET.get('patient')
        if patient_id:
            try:
                patient = Patient.objects.get(
                    pk=patient_id)
                initial['patient'] = patient
            except Patient.DoesNotExist:
                pass
        return initial
    
    def form_valid(self, form):
        # form.# instance.tenant = self.request.user.tenant  # Temporarily commented out  # Temporarily commented out
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
        return Appointment.objects.filter()
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['hospital'] = self.request.session.get('selected_hospital_code')
        return kwargs
    
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
@require_hospital_selection
@require_hospital_selection
def quick_appointment_create(request):
    """Quick appointment creation via HTMX"""
    if request.method == 'POST':
        form = QuickAppointmentForm(request.POST, hospital=request.session.get("selected_hospital_code"))
        if form.is_valid():
            appointment = form.save(commit=False)
            # appointment.tenant = request.user.tenant  # Temporarily commented out
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
        form = QuickAppointmentForm(hospital=request.session.get("selected_hospital_code"))
    
    return render(request, 'appointments/quick_create.html', {'form': form})


@login_required
@require_hospital_selection
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
def get_available_time_slots(request):
    """Get available time slots for a doctor on a specific date"""
    doctor_id = request.GET.get('doctor_id')
    date = request.GET.get('date')
    
    if not doctor_id or not date:
        return JsonResponse({'slots': []})
    
    try:
        doctor = Doctor.objects.get(id=doctor_id)
        appointment_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Generate time slots (9 AM to 5 PM, 30-minute intervals)
        slots = []
        current_time = datetime.combine(appointment_date, datetime.min.time().replace(hour=9))
        end_time = datetime.combine(appointment_date, datetime.min.time().replace(hour=17))
        
        # Get existing appointments for this doctor and date
        existing_appointments = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=appointment_date,
            status__in=['SCHEDULED', 'CONFIRMED', 'CHECKED_IN', 'IN_PROGRESS']
        ).values_list('appointment_time', flat=True)
        
        while current_time < end_time:
            time_slot = current_time.time()
            is_available = time_slot not in existing_appointments
            
            slots.append({
                'time': time_slot.strftime('%H:%M'),
                'display': time_slot.strftime('%I:%M %p'),
                'available': is_available
            })
            
            current_time += timedelta(minutes=30)
        
        return JsonResponse({'slots': slots})
        
    except (Doctor.DoesNotExist, ValueError):
        return JsonResponse({'slots': []})


@login_required
@require_hospital_selection
def reschedule_appointment(request, pk):
    """Reschedule an appointment"""
    appointment = get_object_or_404(
        Appointment, 
        id=pk, 
        tenant=request.user.tenant
    )
    
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
    appointment = get_object_or_404(
        Appointment,
        id=pk,
        tenant=request.user.tenant
    )
    
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
        tenant=request.user.tenant,
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
        tenant=request.user.tenant,
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
@require_hospital_selection
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
        'doctors': Doctor.objects.filter(user__hospital=request.user.hospital, is_active=True),
        'appointment_types': AppointmentType.objects.filter(hospital=request.user.hospital, is_active=True)
    }
    
    return render(request, 'appointments/calendar.html', context)


# Enhanced UI Views
@login_required
@require_hospital_selection
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
    appointments = Appointment.objects.filter(
        ).select_related('patient', 'doctor', 'created_by')
    
    # Apply filters
    if search:
        appointments = appointments.filter(
            Q(patient__first_name__icontains=search) |
            Q(patient__last_name__icontains=search) |
            Q(doctor__first_name__icontains=search) |
            Q(doctor__last_name__icontains=search) |
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
    doctors = Doctor.objects.filter(user__hospital=request.user.hospital, is_active=True)
    
    # Statistics
    stats = {
        'total': Appointment.objects.filter().count(),
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
    
    return render(request, 'appointments/appointment_list_enhanced.html', context)


@login_required
@require_hospital_selection
def appointment_create_enhanced(request):
    """Enhanced appointment creation view with wizard UI"""
    if request.method == 'POST':
        form = AppointmentForm(request.POST, hospital=request.session.get("selected_hospital_code"))
        if form.is_valid():
            appointment = form.save(commit=False)
            # appointment.tenant = request.user.tenant  # Temporarily commented out
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
        # Get tenant from session instead of user.tenant
        tenant_code = request.session.get('selected_hospital_code')
        form = AppointmentForm(hospital=tenant_code)
        
        # Pre-populate with patient if provided
        patient_id = request.GET.get('patient')
        if patient_id:
            try:
                # Remove tenant filtering temporarily since field is commented out
                patient = Patient.objects.get(pk=patient_id, is_active=True)
                form.fields['patient'].initial = patient
            except Patient.DoesNotExist:
                pass
    
    context = {
        'form': form,
        # Temporarily remove hospital filtering since fields are commented out
        'patients': Patient.objects.filter(is_active=True)[:50],
        'doctors': Doctor.objects.filter(is_active=True),
        'appointment_types': AppointmentType.objects.filter(is_active=True),
    }
    
    return render(request, 'appointments/appointment_create_enhanced.html', context)


@login_required
def appointment_detail_enhanced(request, pk):
    """Enhanced appointment detail view with modern UI"""
    # Get selected hospital from session
    selected_hospital_id = request.session.get('selected_hospital_id')
    
    appointment = get_object_or_404(
        Appointment.objects.select_related('patient', 'doctor', 'created_by'),
        pk=pk
    )
    
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
    
    return render(request, 'appointments/appointment_detail_enhanced.html', context)


@login_required
@require_hospital_selection
def appointment_calendar(request):
    """Enhanced calendar view"""
    # Get selected hospital from session
    selected_hospital_id = request.session.get('selected_hospital_id')
    
    # Filter doctors and appointment types by selected hospital
    doctors = Doctor.objects.filter(is_active=True) if selected_hospital_id else Doctor.objects.none()
    appointment_types = AppointmentType.objects.filter(is_active=True) if selected_hospital_id else AppointmentType.objects.none()
    
    # Get today's appointments for sidebar
    today = timezone.now().date()
    today_appointments = Appointment.objects.filter(
        appointment_date=today
    ).select_related('patient', 'doctor').order_by('appointment_time') if selected_hospital_id else Appointment.objects.none()
    
    context = {
        'doctors': doctors,
        'appointment_types': appointment_types,
        'today_appointments': today_appointments,
    }
    
    return render(request, 'appointments/appointment_calendar_enhanced.html', context)


@login_required
@require_hospital_selection
def calendar_events(request):
    """JSON endpoint for calendar events"""
    start = request.GET.get('start')
    end = request.GET.get('end')
    doctor_id = request.GET.get('doctor')
    
    appointments = Appointment.objects.filter(
        ).select_related('patient', 'doctor')
    
    if start:
        appointments = appointments.filter(appointment_date__gte=start)
    if end:
        appointments = appointments.filter(appointment_date__lte=end)
    if doctor_id:
        appointments = appointments.filter(doctor_id=doctor_id)
    
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
@require_hospital_selection
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
@require_hospital_selection
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
@require_hospital_selection
def get_available_time_slots(request):
    """Enhanced time slots endpoint"""
    doctor_id = request.GET.get('doctor_id')
    date = request.GET.get('date')
    
    if not doctor_id or not date:
        return JsonResponse({'slots': []})
    
    try:
        doctor = Doctor.objects.get(id=doctor_id, user__hospital=request.user.hospital)
        appointment_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Generate time slots
        slots = []
        start_hour = 9  # 9 AM
        end_hour = 17   # 5 PM
        interval = 30   # 30 minutes
        
        # Get existing appointments
        existing = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=appointment_date,
            status__in=['SCHEDULED', 'CONFIRMED', 'CHECKED_IN', 'IN_PROGRESS']
        ).values_list('appointment_time', flat=True)
        
        existing_times = [t.strftime('%H:%M') for t in existing if t]
        
        current_hour = start_hour
        current_minute = 0
        
        while current_hour < end_hour:
            time_str = f"{current_hour:02d}:{current_minute:02d}"
            time_obj = datetime.strptime(time_str, '%H:%M').time()
            
            slots.append({
                'time': time_str,
                'display': time_obj.strftime('%I:%M %p'),
                'available': time_str not in existing_times
            })
            
            current_minute += interval
            if current_minute >= 60:
                current_minute = 0
                current_hour += 1
        
        return JsonResponse({'slots': slots})
        
    except (Doctor.DoesNotExist, ValueError):
        return JsonResponse({'slots': []})


@login_required
def appointment_detail_modal(request, pk):
    """Modal view for appointment details"""
    appointment = get_object_or_404(
        Appointment.objects.select_related('patient', 'doctor'),
        pk=pk,
        tenant=request.user.tenant
    )
    
    context = {
        'appointment': appointment,
        'can_reschedule': appointment.can_be_rescheduled(),
        'can_cancel': appointment.can_be_cancelled(),
    }
    
    return render(request, 'appointments/appointment_detail_modal.html', context)


@login_required
def start_consultation(request, pk):
    """Start consultation for an appointment"""
    appointment = get_object_or_404(
        Appointment,
        pk=pk,
        tenant=request.user.tenant,
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
    appointment = get_object_or_404(
        Appointment,
        pk=pk,
        tenant=request.user.tenant
    )
    
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
    
    appointments = Appointment.objects.filter(
        ).select_related('patient', 'doctor').order_by('-appointment_date')
    
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
    """Print appointment with QR code"""
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Generate QR code for the appointment
    appointment_qr_code = document_qr_generator.generate_appointment_qr(appointment, request)
    
    context = {
        'appointment': appointment,
        'appointment_qr_code': appointment_qr_code,
        'hospital': request.user.hospital,
        'today': timezone.now().date(),
    }
    
    return render(request, 'appointments/print_appointment.html', context)


@login_required
def export_appointment_pdf(request, pk):
    """Export single appointment to PDF"""
    # Redirect to print view for now
    return redirect('appointments:print_appointment', pk=pk)