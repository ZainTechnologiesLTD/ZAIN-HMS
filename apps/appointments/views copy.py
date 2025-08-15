# appointments/views.py

from datetime import datetime, timedelta
from venv import logger
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import CreateView, ListView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.db.models import Q
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import transaction
from doctors.models import Doctor, DoctorSchedule
from patients.models import Patient
from .forms import AppointmentForm
from .models import Appointment
import logging
logger = logging.getLogger(__name__)

class AppointmentUpdateView(LoginRequiredMixin, UpdateView):
    model = Appointment
    form_class = AppointmentForm
    template_name = 'appointments/appointment_edit.html'
    success_url = reverse_lazy('appointments:appointment_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['specializations'] = Doctor.SPECIALIZATION_CHOICES
        context['appointment_types'] = Appointment.APPOINTMENT_TYPES
        context['today'] = timezone.now().date()
        return context

    def form_valid(self, form):
        logger.debug(f"POST data: {self.request.POST}")
        logger.debug(f"Doctor ID from POST: {self.request.POST.get('doctor')}")
        try:
            with transaction.atomic():
                appointment = form.save(commit=False)
                
                # Get the form data
                patient_id = self.request.POST.get('patient')
                doctor_id = self.request.POST.get('doctor')
                time_slot = self.request.POST.get('time')
                reason = self.request.POST.get('reason')
                appointment_type = self.request.POST.get('appointment_type')
                
                # Set is_opd based on appointment type
                appointment.is_opd = (appointment_type == 'OPD')

                # Validate required fields
                if not all([patient_id, doctor_id, time_slot, reason, appointment_type]):
                    return self.form_invalid(form)

                # Get the patient and doctor instances
                patient = get_object_or_404(Patient, id=patient_id)
                doctor = get_object_or_404(Doctor, id=doctor_id)

                # Update appointment instance
                appointment.patient = patient
                appointment.doctor = doctor
                appointment.date_time = timezone.make_aware(
                    datetime.strptime(time_slot, '%Y-%m-%d %H:%M')
                )
                appointment.reason = reason
                appointment.appointment_type = appointment_type
                
                appointment.save()

                messages.success(self.request, 'Appointment updated successfully.')
                return super().form_valid(form)

        except Exception as e:
            logger.error(f"Error updating appointment: {str(e)}")
            form.add_error(None, "Error updating appointment. Please try again.")
            return self.form_invalid(form)
@require_POST
def cancel_appointment(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Optional: Check if the user has permission to cancel the appointment
    # For example, only staff members can cancel appointments
    if not request.user.is_staff:
        messages.error(request, "You do not have permission to cancel appointments.")
        return redirect('appointments:appointment_detail', pk=pk)
    
    if appointment.status in ['CANCELLED', 'COMPLETED']:
        messages.info(request, "This appointment cannot be cancelled.")
    else:
        appointment.status = 'CANCELLED'
        appointment.save()
        messages.success(request, "Appointment has been cancelled successfully.")
    
    return redirect('appointments:appointment_list')  # Redirect to the appointment list

class AppointmentListView(LoginRequiredMixin, ListView):
    """
    View to list all appointments
    """
    model = Appointment
    template_name = 'appointments/appointment_list.html'
    context_object_name = 'appointments'
    paginate_by = 20  # Optional: add pagination

    def get_queryset(self):
        """
        Customize the queryset to order by most recent appointments
        """
        return Appointment.objects.all().order_by('-date_time')

    def get_context_data(self, **kwargs):
        """
        Add additional context data
        """
        context = super().get_context_data(**kwargs)
        context['title'] = 'Appointments List'
        return context

class AppointmentDetailView(LoginRequiredMixin, DetailView):
    """
    View to show details of a specific appointment
    """
    model = Appointment
    template_name = 'appointments/appointment_detail.html'



class AppointmentCreateView(LoginRequiredMixin, CreateView):
    model = Appointment
    form_class = AppointmentForm
    template_name = 'appointments/appointment_create.html'
    success_url = reverse_lazy('appointments:appointment_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['specializations'] = Doctor.SPECIALIZATION_CHOICES
        context['appointment_types'] = Appointment.APPOINTMENT_TYPES
        context['today'] = timezone.now().date()
        return context

    def form_valid(self, form):
        try:
            logger.debug("Starting form_valid")
            logger.debug(f"POST data: {self.request.POST}")
            
            with transaction.atomic():
                # Get form data
                patient_id = self.request.POST.get('patient')
                doctor_id = self.request.POST.get('doctor')
                time_slot = self.request.POST.get('time')
                reason = self.request.POST.get('reason')
                appointment_type = self.request.POST.get('appointment_type')

                # Debug logging
                logger.debug(f"Patient ID: {patient_id}")
                logger.debug(f"Doctor ID: {doctor_id}")
                logger.debug(f"Time slot: {time_slot}")
                logger.debug(f"Appointment type: {appointment_type}")

                # Validate required fields
                if not all([patient_id, doctor_id, time_slot, appointment_type]):
                    messages.error(self.request, 'All required fields must be filled.')
                    return self.form_invalid(form)

                try:
                    # Get the doctor and patient instances
                    doctor = Doctor.objects.get(doctor_id=doctor_id)
                    patient = Patient.objects.get(id=patient_id)
                    logger.debug(f"Found doctor: {doctor}")
                    logger.debug(f"Found patient: {patient}")

                    # Parse and validate the datetime
                    try:
                        naive_datetime = datetime.strptime(time_slot, '%Y-%m-%d %H:%M')
                        # Get the current timezone
                        current_tz = timezone.get_current_timezone()
                        # Make the datetime timezone-aware
                        aware_datetime = timezone.make_aware(naive_datetime, current_tz)
                        
                        # Validate that the appointment is not in the past
                        if aware_datetime < timezone.now():
                            raise ValidationError("Cannot create appointments in the past")
                            
                    except (ValueError, TypeError) as e:
                        raise ValidationError(f"Invalid date format: {str(e)}")

                    # Create the appointment
                    appointment = form.save(commit=False)
                    appointment.doctor = doctor
                    appointment.patient = patient
                    appointment.date_time = aware_datetime
                    appointment.reason = reason
                    appointment.appointment_type = appointment_type
                    appointment.created_by = self.request.user
                    
                    # Validate and save
                    appointment.full_clean()
                    appointment.save()
                    logger.debug("Appointment saved successfully")

                    messages.success(self.request, 'Appointment created successfully.')
                    return redirect(self.success_url)

                except Doctor.DoesNotExist:
                    messages.error(self.request, f'Doctor with ID {doctor_id} not found.')
                    return self.form_invalid(form)
                except Patient.DoesNotExist:
                    messages.error(self.request, f'Patient with ID {patient_id} not found.')
                    return self.form_invalid(form)
                except ValidationError as e:
                    messages.error(self.request, str(e))
                    return self.form_invalid(form)

        except Exception as e:
            logger.error(f"Error creating appointment: {str(e)}")
            messages.error(self.request, f"Error creating appointment: {str(e)}")
            return self.form_invalid(form)

    def form_invalid(self, form):
        logger.error(f"Form errors: {form.errors}")
        messages.error(self.request, f"Form validation failed: {form.errors}")
        return super().form_invalid(form)
@require_GET
def search_patients(request):
    """
    Search for patients based on name, phone, or patient ID
    """
    name = request.GET.get('search_name', '').strip()
    phone = request.GET.get('search_phone', '').strip()
    patient_id = request.GET.get('search_patient_id', '').strip()
    
    queryset = Patient.objects.all()
    
    # Apply filters based on search parameters
    if name:
        queryset = queryset.filter(
            Q(first_name__icontains=name) | 
            Q(last_name__icontains=name)
        )
    if phone:
        queryset = queryset.filter(phone_number__icontains=phone)
    if patient_id:
        queryset = queryset.filter(patient_id__icontains=patient_id)
    
    # Limit to first 5 results
    patients = queryset.distinct()[:5]
    
    # If no patients found, return a message
    if not patients.exists():
        return HttpResponse('<p class="text-muted">No patients found.</p>')
    
    # Render patient list as HTML
    html = '<ul class="list-group">'
    for patient in patients:
        html += f'''
            <li class="list-group-item list-group-item-action" 
                onclick="selectPatient('{patient.id}', '{patient.get_full_name()}')">
                {patient.get_full_name()} (ID: {patient.patient_id}) - {patient.phone_number}
            </li>
        '''
    html += '</ul>'
    
    return HttpResponse(html)

@require_GET
def get_doctors(request):
    """
    Fetch doctors based on selected specialization
    """
    specialization = request.GET.get('specialization')
    
    if not specialization:
        return HttpResponse('<option value="">Select a specialization</option>')
    
    # Filter active doctors by specialization
    doctors = Doctor.objects.filter(
        specialization=specialization,
        is_active=True
    )
    
    # If no doctors found
    if not doctors.exists():
        return HttpResponse('<option value="">No doctors available</option>')
    
   
    return render(request, 'appointments/doctor_options.html', {
        'doctors': doctors   })

@require_POST
def check_availability(request):
    """
    Check doctor's availability for a specific date and time
    """
    try:
        doctor_id = request.POST.get('doctor')
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        
        # Validate inputs
        if not all([doctor_id, date_str, time_str]):
            return JsonResponse({
                'status': 'error',
                'message': 'Missing required fields'
            }) 
        doctor = get_object_or_404(Doctor, id=doctor_id)
        date_time = timezone.make_aware(
            datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M'))
        
        # Parse date
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid date format'
            }, status=400)
        
        # Fetch doctor and check schedule
        doctor = get_object_or_404(Doctor, id=doctor_id)
        
        # Prevent booking in the past
        if date < timezone.now().date():
            return JsonResponse({
                'status': 'error',
                'message': 'Cannot book appointments in the past'
            }, status=400)
        
        # Get existing appointments on this date
        existing_appointments = Appointment.objects.filter(
            doctor=doctor,
            date_time__date=date
        )
        
        # Generate available time slots
        available_slots = _generate_available_slots(doctor, date, existing_appointments)
        
        return render_to_string('appointments/time_slots.html', 
                                 {'slots': available_slots}, 
                                 request=request)
    
    except Exception as e:
        logger.error(f"Availability check error: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'An unexpected error occurred'
        }, status=500)


    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })


def _generate_available_slots(doctor, date, existing_appointments):
    """
    Helper function to generate available time slots
    """
    # You would typically have this logic in your Doctor or DoctorSchedule model
    # This is a simplified example
    all_possible_slots = [
        '09:00', '09:30', '10:00', '10:30', '11:00', '11:30', 
        '14:00', '14:30', '15:00', '15:30', '16:00', '16:30'
    ]
    
    # Remove slots that are already booked
    booked_times = set(
        appt.date_time.strftime('%H:%M') 
        for appt in existing_appointments
    )
    
    available_slots = [
        slot for slot in all_possible_slots 
        if slot not in booked_times
    ]
    
    return available_slots


@require_GET
def upcoming_appointments(request):
    # Get today's date
    today = timezone.now()
    
    # Get appointments that are upcoming (today and future) and not cancelled
    upcoming = Appointment.objects.filter(
        Q(date_time__date__gte=today.date()) & 
        Q(status='SCHEDULED')
    ).select_related(
        'doctor', 
        'patient'
    ).order_by(
        'date_time'
    )[:5]  # Limit to 5 upcoming appointments
    
    return render(request, 'appointments/upcoming_list.html', {
        'appointments': upcoming
    })
@require_GET
def patient_appointment_history(request, patient_id):
    """
    View appointment history for a specific patient
    """
    patient = get_object_or_404(Patient, id=patient_id)
    
    appointments = Appointment.objects.filter(
        patient=patient
    ).order_by('-date_time')
    
    return render(request, 'appointments/patient_history.html', {
        'patient': patient, 
        'appointments': appointments
    })
@require_GET
def get_doctor_schedule(request):
    """
    Retrieve all time slots (both available and booked) for a specific doctor for the next 30 days
    """
    try:
        doctor_id = request.GET.get('doctor')
        if not doctor_id:
            return HttpResponse('<option value="">Select a doctor first</option>')
        
        doctor = get_object_or_404(Doctor, doctor_id=doctor_id)
        today = timezone.now()
        end_date = today + timedelta(days=30)  # Look ahead 30 days
        
        all_slots = []
        current_date = today.date()
        
        # Look for slots in the next 30 days
        while current_date <= end_date.date():
            # Get doctor's schedule for this day
            schedule = DoctorSchedule.objects.filter(
                doctor=doctor,
                day_of_week=current_date.weekday()
            ).first()
            
            if schedule:
                # Get existing appointments for this day
                existing_appointments = Appointment.objects.filter(
                    doctor=doctor,
                    date_time__date=current_date
                )
                
                # Generate time slots based on schedule
                current_time = datetime.combine(current_date, schedule.start_time)
                end_time = datetime.combine(current_date, schedule.end_time)
                
                # Generate 30-minute slots
                while current_time < end_time:
                    # Skip past times for today
                    if current_date == today.date() and current_time.time() <= today.time():
                        current_time += timedelta(minutes=30)
                        continue
                    
                    slot_datetime = timezone.make_aware(current_time)
                    
                    # Check if slot is booked
                    is_booked = existing_appointments.filter(
                        date_time=slot_datetime
                    ).exists()
                    
                    all_slots.append({
                        'datetime': slot_datetime,
                        'display': f"{slot_datetime.strftime('%A, %B %d, %Y')} at {slot_datetime.strftime('%I:%M %p')}",
                        'is_booked': is_booked
                    })
                    
                    current_time += timedelta(minutes=30)
            
            current_date += timedelta(days=1)
        
        if not all_slots:
            return HttpResponse('<option value="">No slots available in the next 30 days</option>')
        
        # Sort slots by datetime
        all_slots.sort(key=lambda x: x['datetime'])
        
        return render(request, 'appointments/time_slots.html', {
            'slots': all_slots
        })
    
    except Exception as e:
        logger.error(f"Get doctor schedule error: {str(e)}")
        return HttpResponse('<option value="">Error loading time slots</option>')
def quick_schedule(request):
    logger.info(f"Quick schedule request: {request.POST}")
    if request.method == 'GET':
        context = {
            'specializations': Doctor.SPECIALIZATION_CHOICES,
            'appointment_types': Appointment.APPOINTMENT_TYPES,
            'today': timezone.now().date(),
        }
        return render(request, 'appointments/quick_schedule_form.html', context)

    elif request.method == 'POST':
        try:
            # Input validation could be moved to a form
            patient_id = request.POST.get('patient')
            logger.debug(f"Received Patient ID (Primary Key): {patient_id}")
            doctor_id = request.POST.get('doctor')
            date = request.POST.get('date')
            time = request.POST.get('time')
            reason = request.POST.get('reason')
            appointment_type = request.POST.get('appointment_type')
# Debug logging
            logger.debug(f"Received doctor_id: {doctor_id}")


            # Validate inputs
            if not all([patient_id, doctor_id, date, time, reason, appointment_type]):
                raise ValidationError('All fields are required')

            # Fetch patient by primary key
            patient = get_object_or_404(Patient, id=patient_id)
            doctor = get_object_or_404(Doctor, id=doctor_id)

            # Robust datetime parsing with error handling
            try:
                date_time = timezone.make_aware(
                    datetime.strptime(f"{date} {time}", '%Y-%m-%d %H:%M')
                )
            except ValueError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid date or time format'
                }, status=400)

            # Use transaction to ensure atomic operation
            with transaction.atomic():
                # Check doctor availability
                schedule = DoctorSchedule.objects.filter(
                    doctor=doctor,
                    day_of_week=date_time.weekday()
                ).first()

                if not schedule or not schedule.is_available(date_time.date(), date_time.time()):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Selected time slot is no longer available'
                    }, status=400)

                # Check for conflicting appointments
                conflicting_appointments = Appointment.objects.filter(
                    doctor=doctor,
                    date_time__range=[
                        date_time - timedelta(minutes=30),
                        date_time + timedelta(minutes=30)
                    ]
                )
                if conflicting_appointments.exists():
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Conflicting appointment exists'
                    }, status=400)

                # Create appointment
                appointment = Appointment.objects.create(
                    patient=patient,
                    doctor=doctor,
                    date_time=date_time,
                    reason=reason,
                    created_by=request.user,
                    appointment_type=appointment_type,
                    is_opd=(appointment_type == 'OPD')
                )

                
            logger.info(f"Appointment created successfully: {appointment.pk}")
            return JsonResponse({
                'status': 'success',
                'message': 'Appointment scheduled successfully',
                'redirect': f'/appointments/{appointment.pk}/'
            })

        except ValidationError as ve:
            logger.warning(f"Validation error during appointment scheduling: {ve}")
            return JsonResponse({
                'status': 'error',
                'message': str(ve)
            }, status=400)
        except Exception as e:
            # Log the error
            logger.error(f"Appointment scheduling error: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': 'An unexpected error occurred'
            }, status=500)

    # Method not allowed
    logger.warning(f"Invalid request method for quick_schedule: {request.method}")
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=405)

def dashboard(request):
    # Get upcoming appointments for initial load
    today = timezone.now()
    upcoming_appointments = Appointment.objects.filter(
        Q(date_time__date__gte=today.date()) & 
        Q(status='SCHEDULED')
    ).select_related(
        'doctor', 
        'patient'
    ).order_by(
        'date_time'
    )[:5]

    context = {
        'upcoming_appointments': upcoming_appointments,
        # ... other context data ...
    }
    return render(request, 'dashboard.html', context)