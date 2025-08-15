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

class AppointmentListView(LoginRequiredMixin, ListView):
    """List appointments with filtering and search"""
    model = Appointment
    template_name = 'appointments/appointment_list.html'
    context_object_name = 'appointments'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Appointment.objects.filter(
            hospital=self.request.user.hospital
        ).select_related('patient', 'doctor', 'appointment_type', 'created_by')
        
        # Apply filters from search form
        form = AppointmentSearchForm(self.request.GET, hospital=self.request.user.hospital)
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
            self.request.GET, 
            hospital=self.request.user.hospital
        )
        
        # Statistics
        today = timezone.now().date()
        context['today_appointments'] = Appointment.objects.filter(
            hospital=self.request.user.hospital,
            appointment_date=today
        ).count()
        
        context['pending_appointments'] = Appointment.objects.filter(
            hospital=self.request.user.hospital,
            status='SCHEDULED'
        ).count()
        
        context['completed_today'] = Appointment.objects.filter(
            hospital=self.request.user.hospital,
            appointment_date=today,
            status='COMPLETED'
        ).count()
        
        return context


class AppointmentDetailView(LoginRequiredMixin, DetailView):
    """Detailed appointment view"""
    model = Appointment
    template_name = 'appointments/appointment_detail.html'
    context_object_name = 'appointment'
    
    def get_queryset(self):
        return Appointment.objects.filter(
            hospital=self.request.user.hospital
        ).select_related('patient', 'doctor', 'appointment_type', 'created_by')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['history'] = self.object.history.all()
        context['can_reschedule'] = self.object.can_be_rescheduled()
        context['can_cancel'] = self.object.can_be_cancelled()
        context['reschedule_form'] = RescheduleAppointmentForm(appointment=self.object)
        context['cancel_form'] = CancelAppointmentForm()
        return context


class AppointmentCreateView(LoginRequiredMixin, CreateView):
    """Create new appointment"""
    model = Appointment
    form_class = AppointmentForm
    template_name = 'appointments/appointment_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['hospital'] = self.request.user.hospital
        return kwargs
    
    def form_valid(self, form):
        form.instance.hospital = self.request.user.hospital
        form.instance.created_by = self.request.user
        
        # Set default appointment type if not specified
        if not form.instance.appointment_type:
            default_type = AppointmentType.objects.filter(
                hospital=self.request.user.hospital,
                name='General Consultation'
            ).first()
            if default_type:
                form.instance.appointment_type = default_type
        
        messages.success(self.request, 'Appointment scheduled successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('appointments:detail', kwargs={'pk': self.object.pk})


class AppointmentUpdateView(LoginRequiredMixin, UpdateView):
    """Update appointment"""
    model = Appointment
    form_class = AppointmentForm
    template_name = 'appointments/appointment_form.html'
    
    def get_queryset(self):
        return Appointment.objects.filter(hospital=self.request.user.hospital)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['hospital'] = self.request.user.hospital
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
def quick_appointment_create(request):
    """Quick appointment creation via HTMX"""
    if request.method == 'POST':
        form = QuickAppointmentForm(request.POST, hospital=request.user.hospital)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.hospital = request.user.hospital
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
        form = QuickAppointmentForm(hospital=request.user.hospital)
    
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
        doctor = Doctor.objects.get(id=doctor_id, hospital=request.user.hospital)
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
        doctor = Doctor.objects.get(id=doctor_id, hospital=request.user.hospital)
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
def reschedule_appointment(request, pk):
    """Reschedule an appointment"""
    appointment = get_object_or_404(
        Appointment, 
        id=pk, 
        hospital=request.user.hospital
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
        hospital=request.user.hospital
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
        hospital=request.user.hospital,
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
        hospital=request.user.hospital,
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
        hospital=request.user.hospital,
        appointment_date__month=today.month,
        appointment_date__year=today.year
    ).select_related('patient', 'doctor', 'appointment_type')
    
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
        'doctors': Doctor.objects.filter(hospital=request.user.hospital, is_active=True),
        'appointment_types': AppointmentType.objects.filter(hospital=request.user.hospital, is_active=True)
    }
    
    return render(request, 'appointments/calendar.html', context)