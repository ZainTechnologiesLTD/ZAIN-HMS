# doctors/views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone
from datetime import datetime, timedelta
from apps.accounts.models import CustomUser as User
from apps.accounts.services import UserManagementService
# from tenants.permissions import  # Temporarily commented TenantFilterMixin
from .models import Doctor
from apps.core.mixins import TenantSafeMixin, RequireHospitalSelectionMixin
from .forms import DoctorForm, DoctorSearchForm


class DoctorListView(TenantSafeMixin, ListView):  # TenantFilterMixin temporarily commented:
    model = Doctor
    template_name = 'doctors/doctor_list.html'
    context_object_name = 'doctors'
    paginate_by = 20
    required_roles = ['admin', 'receptionist', 'doctor', 'nurse']
    tenant_filter_field = 'user__tenant'  # Doctor is linked via user

    def get_queryset(self):
        queryset = self.filter_by_tenant(Doctor.objects.filter(is_active=True))

        # Search functionality
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(specialization__icontains=search)
                | Q(license_number__icontains=search)
                | Q(email__icontains=search)
                | Q(phone_number__icontains=search)
            )

        # Filter by specialization
        specialization = self.request.GET.get('specialization')
        if specialization:
            queryset = queryset.filter(specialization=specialization)

        return queryset.order_by('first_name', 'last_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = DoctorSearchForm(self.request.GET)
        base_queryset = self.filter_by_tenant(Doctor.objects.filter(is_active=True))
        context['total_doctors'] = base_queryset.count()
        context['specializations'] = base_queryset.values_list('specialization', flat=True).distinct()
        return context


class DoctorDetailView(TenantSafeMixin, DetailView):  # TenantFilterMixin temporarily commented:
    model = Doctor
    template_name = 'doctors/doctor_detail.html'
    context_object_name = 'doctor'
    required_roles = ['admin', 'receptionist', 'doctor', 'nurse']
    tenant_filter_field = 'user__tenant'  # Doctor is linked via user
    
    def get_queryset(self):
        return self.filter_by_tenant(Doctor.objects.all())


class DoctorCreateView(RequireHospitalSelectionMixin, CreateView):
    model = Doctor
    form_class = DoctorForm
    template_name = 'doctors/doctor_form.html'
    success_url = reverse_lazy('doctors:doctor_list')
    required_roles = ['admin', 'hr_manager']
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Get tenant from session selected hospital code instead of user.tenant
        tenant_code = self.request.session.get('selected_hospital_code')
        kwargs['hospital'] = tenant_code
        return kwargs
    
    def form_valid(self, form):
        try:
            doctor = form.save(commit=False)
            
            # Use UserManagementService to create user account
            tenant_code = self.request.session.get('selected_hospital_code')
            user = UserManagementService.create_user_account(
                email=doctor.email,
                first_name=doctor.first_name,
                last_name=doctor.last_name,
                role='DOCTOR',
                tenant_code=tenant_code,
                created_by=self.request.user,
                additional_data={
                    'specialization': doctor.specialization,
                    'license_number': doctor.license_number,
                    'phone_number': doctor.phone_number,
                }
            )
            
            # Link the doctor to the created user
            doctor.user = user
            doctor.save()
            
            messages.success(
                self.request,
                f'Doctor {doctor.get_full_name()} created successfully! '
                f'Login credentials have been sent to {doctor.email}.'
            )
            
            return super().form_valid(form)
            
        except Exception as e:
            messages.error(
                self.request,
                f'Error creating doctor account: {str(e)}'
            )
            return self.form_invalid(form)


class DoctorUpdateView(TenantSafeMixin, UpdateView):  # TenantFilterMixin temporarily commented:
    model = Doctor
    form_class = DoctorForm
    template_name = 'doctors/doctor_form.html'
    success_url = reverse_lazy('doctors:doctor_list')
    required_roles = ['admin', 'hr_manager']
    tenant_filter_field = 'user__tenant'  # Doctor is linked via user
    
    def get_queryset(self):
        return self.filter_by_tenant(Doctor.objects.all())
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        tenant_code = self.request.session.get('selected_hospital_code')
        kwargs['hospital'] = tenant_code
        return kwargs
    
    def form_valid(self, form):
        doctor = form.save()
        
        # Update the linked user's information if email or name changed
        if doctor.user:
            user = doctor.user
            user.email = doctor.email
            user.first_name = doctor.first_name
            user.last_name = doctor.last_name
            user.save()
        
        messages.success(self.request, 'Doctor profile updated successfully!')
        return super().form_valid(form)


class DoctorDeleteView(TenantSafeMixin, DeleteView):  # TenantFilterMixin temporarily commented:
    model = Doctor
    template_name = 'doctors/doctor_confirm_delete.html'
    success_url = reverse_lazy('doctors:doctor_list')
    context_object_name = 'doctor'
    required_roles = ['admin']  # Only admin can delete doctors
    tenant_filter_field = 'user__tenant'  # Doctor is linked via user
    
    def get_queryset(self):
        return self.filter_by_tenant(Doctor.objects.all())
    
    def delete(self, request, *args, **kwargs):
        doctor = self.get_object()
        doctor_name = doctor.get_full_name()
        
        # Also deactivate or delete the associated user account
        if doctor.user:
            doctor.user.is_active = False
            doctor.user.save()
        
        messages.success(request, f'Doctor {doctor_name} has been deleted successfully!')
        return super().delete(request, *args, **kwargs)


class CreateUserForDoctorView(View):
    """Create a user account for an existing doctor"""
    required_roles = ['admin', 'hr_manager']
    
    def post(self, request, pk):
        try:
            doctor = get_object_or_404(Doctor, pk=pk)
            
            # Check if doctor already has a user
            if doctor.user:
                messages.warning(request, f'Doctor {doctor.get_full_name()} already has a user account.')
                return redirect('doctors:doctor_detail', pk=pk)
            
            # Create user account for the doctor
            user = UserManagementService.create_user_for_existing_doctor(
                doctor_id=doctor.id,
                created_by_user=request.user
            )
            
            messages.success(
                request,
                f'User account created successfully for Dr. {doctor.get_full_name()}! '
                f'Login credentials have been sent to {doctor.email}.'
            )
            
        except Exception as e:
            messages.error(request, f'Error creating user account: {str(e)}')
        
        return redirect('doctors:doctor_detail', pk=pk)


class LinkDoctorUserView(View):
    """Link an existing user to an existing doctor"""
    required_roles = ['admin', 'hr_manager']
    
    def get(self, request, pk):
        doctor = get_object_or_404(Doctor, pk=pk)
        
        # Check if doctor already has a user
        if doctor.user:
            messages.warning(request, f'Doctor {doctor.get_full_name()} already has a linked user account.')
            return redirect('doctors:doctor_detail', pk=pk)
        
        # Get available users (DOCTOR role without linked doctor)
        tenant_code = request.session.get('selected_hospital_code')
        # For now, get all users with DOCTOR role since tenant field is commented out
        available_users = User.objects.filter(
            role='DOCTOR',
            doctor__isnull=True  # Users not already linked to a doctor
        ).order_by('first_name', 'last_name')
        
        context = {
            'doctor': doctor,
            'available_users': available_users
        }
        
        return render(request, 'doctors/link_user.html', context)
    
    def post(self, request, pk):
        try:
            doctor = get_object_or_404(Doctor, pk=pk)
            user_id = request.POST.get('user_id')
            
            if not user_id:
                messages.error(request, 'Please select a user to link.')
                return redirect('doctors:link_user', pk=pk)
            
            # Link the user to the doctor
            UserManagementService.link_user_to_doctor(
                user_id=user_id,
                doctor_id=doctor.id,
                linked_by_user=request.user
            )
            
            messages.success(
                request,
                f'User successfully linked to Dr. {doctor.get_full_name()}!'
            )
            
        except Exception as e:
            messages.error(request, f'Error linking user: {str(e)}')
        
        return redirect('doctors:doctor_detail', pk=pk)


@login_required
@require_POST
def unlink_doctor_user(request, pk):
    """Unlink user from doctor (AJAX endpoint)"""
    try:
        doctor = get_object_or_404(Doctor, pk=pk)
        
        if not doctor.user:
            return JsonResponse({'success': False, 'error': 'Doctor has no linked user account.'})
        
        # Check permissions
        if not (request.user.role in ['ADMIN', 'SUPERADMIN'] or request.user.is_superuser):
            return JsonResponse({'success': False, 'error': 'Permission denied.'})
        
        user_name = doctor.user.get_full_name()
        
        # Unlink
        doctor.user = None
        doctor.save()
        
        return JsonResponse({
            'success': True,
            'message': f'User {user_name} has been unlinked from Dr. {doctor.get_full_name()}'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


class DoctorsWithoutUsersView(ListView):  # TenantFilterMixin temporarily commented:
    """List doctors who don't have user accounts"""
    model = Doctor
    template_name = 'doctors/doctors_without_users.html'
    context_object_name = 'doctors'
    paginate_by = 20
    required_roles = ['admin', 'hr_manager']
    tenant_filter_field = 'user__tenant'
    
    def get_queryset(self):
        # Get doctors without user accounts
        return Doctor.objects.filter(
            user__isnull=True,
            is_active=True
        ).order_by('first_name', 'last_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_doctors_without_users'] = self.get_queryset().count()
        return context


class DoctorDashboardView(LoginRequiredMixin, View):
    """Doctor's personal dashboard showing their appointments and patients"""
    template_name = 'doctors/doctor_dashboard.html'
    
    def get(self, request):
        # Ensure the user is a doctor
        if request.user.role != 'DOCTOR':
            messages.error(request, 'Access denied. This page is only for doctors.')
            return redirect('dashboard:main')
        
        # Get the doctor profile for the current user
        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            messages.error(request, 'Doctor profile not found. Please contact the administrator.')
            return redirect('dashboard:main')
        
        # Get today's date
        today = timezone.now().date()
        
        # Get today's appointments for this doctor
        today_appointments = doctor.appointments.filter(
            appointment_date=today
        ).select_related('patient').order_by('appointment_time')
        
        # Get upcoming appointments (next 7 days)
        upcoming_appointments = doctor.appointments.filter(
            appointment_date__gt=today,
            appointment_date__lte=today + timedelta(days=7),
            status__in=['SCHEDULED', 'CONFIRMED']
        ).select_related('patient').order_by('appointment_date', 'appointment_time')[:10]
        
        # Get recent prescriptions
        recent_prescriptions = doctor.prescriptions.filter(
            created_at__gte=today - timedelta(days=30)
        ).select_related('patient').order_by('-created_at')[:10]
        
        # Get statistics
        stats = {
            'today_appointments': today_appointments.count(),
            'upcoming_appointments': upcoming_appointments.count(),
            'completed_today': today_appointments.filter(status='COMPLETED').count(),
            'pending_today': today_appointments.filter(status__in=['SCHEDULED', 'CONFIRMED', 'CHECKED_IN']).count(),
            'total_patients': doctor.appointments.values('patient').distinct().count(),
            'prescriptions_this_month': doctor.prescriptions.filter(
                created_at__gte=today.replace(day=1)
            ).count(),
        }
        
        context = {
            'doctor': doctor,
            'today_appointments': today_appointments,
            'upcoming_appointments': upcoming_appointments,
            'recent_prescriptions': recent_prescriptions,
            'stats': stats,
            'today_date': today,
        }
        
        return render(request, self.template_name, context)


class DoctorAppointmentsView(LoginRequiredMixin, ListView):
    """List of appointments for the logged-in doctor"""
    model = None  # Will be set dynamically
    template_name = 'doctors/doctor_appointments.html'
    context_object_name = 'appointments'
    paginate_by = 20
    
    def get_queryset(self):
        # Ensure the user is a doctor
        if self.request.user.role != 'DOCTOR':
            return []
        
        # Get the doctor profile for the current user
        try:
            doctor = Doctor.objects.get(user=self.request.user)
        except Doctor.DoesNotExist:
            return []
        
        # Import here to avoid circular imports
        from apps.appointments.models import Appointment
        
        queryset = Appointment.objects.filter(
            doctor=doctor
        ).select_related('patient').order_by('-appointment_date', '-appointment_time')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by date range
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(appointment_date__gte=date_from)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(appointment_date__lte=date_to)
            except ValueError:
                pass
        
        # Search
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(patient__first_name__icontains=search) |
                Q(patient__last_name__icontains=search) |
                Q(chief_complaint__icontains=search) |
                Q(appointment_number__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get the doctor profile
        try:
            doctor = Doctor.objects.get(user=self.request.user)
            context['doctor'] = doctor
        except Doctor.DoesNotExist:
            context['doctor'] = None
        
        # Add filter options
        from apps.appointments.models import Appointment
        context['status_choices'] = Appointment.STATUS_CHOICES
        context['current_status'] = self.request.GET.get('status', '')
        context['current_search'] = self.request.GET.get('q', '')
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')
        
        return context


class DoctorPrescriptionsView(LoginRequiredMixin, ListView):
    """List of prescriptions created by the logged-in doctor"""
    model = None  # Will be set dynamically
    template_name = 'doctors/doctor_prescriptions.html'
    context_object_name = 'prescriptions'
    paginate_by = 20
    
    def get_queryset(self):
        # Ensure the user is a doctor
        if self.request.user.role != 'DOCTOR':
            return []
        
        # Get the doctor profile for the current user
        try:
            doctor = Doctor.objects.get(user=self.request.user)
        except Doctor.DoesNotExist:
            return []
        
        # Import here to avoid circular imports
        from apps.pharmacy.models import Prescription
        
        queryset = Prescription.objects.filter(
            doctor=doctor
        ).select_related('patient').order_by('-created_at')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by date range
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__gte=date_from)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__lte=date_to)
            except ValueError:
                pass
        
        # Search
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(patient__first_name__icontains=search) |
                Q(patient__last_name__icontains=search) |
                Q(prescription_number__icontains=search) |
                Q(diagnosis__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get the doctor profile
        try:
            doctor = Doctor.objects.get(user=self.request.user)
            context['doctor'] = doctor
        except Doctor.DoesNotExist:
            context['doctor'] = None
        
        # Add filter options
        from apps.pharmacy.models import Prescription
        context['status_choices'] = Prescription.STATUS_CHOICES
        context['current_status'] = self.request.GET.get('status', '')
        context['current_search'] = self.request.GET.get('q', '')
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')
        
        return context


class CreatePrescriptionView(RequireHospitalSelectionMixin, LoginRequiredMixin, CreateView):
    """Create a new prescription - doctor only"""
    template_name = 'doctors/create_prescription.html'
    
    def get(self, request, appointment_id=None):
        # Ensure the user is a doctor
        if request.user.role != 'DOCTOR':
            messages.error(request, 'Access denied. Only doctors can create prescriptions.')
            return redirect('dashboard:main')
        
        # Get the doctor profile
        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            messages.error(request, 'Doctor profile not found.')
            return redirect('dashboard:main')
        
        # Get appointment if provided
        appointment = None
        if appointment_id:
            from apps.appointments.models import Appointment
            try:
                appointment = Appointment.objects.get(
                    id=appointment_id,
                    doctor=doctor  # Ensure the appointment belongs to this doctor
                )
            except Appointment.DoesNotExist:
                messages.error(request, 'Appointment not found or access denied.')
                return redirect('doctors:doctor_appointments')
        
        # Get available patients (patients who have had appointments with this doctor)
        patients = []
        if appointment:
            patients = [appointment.patient]
        else:
            from apps.patients.models import Patient
            patient_ids = doctor.appointments.values_list('patient_id', flat=True).distinct()
            patients = Patient.objects.filter(id__in=patient_ids).order_by('first_name', 'last_name')
        
        # Get available medications
        from apps.pharmacy.models import Medicine
        medications = Medicine.objects.filter(
            hospital=request.user.hospital,
            is_active=True
        ).order_by('name')
        
        context = {
            'doctor': doctor,
            'appointment': appointment,
            'patients': patients,
            'medications': medications,
        }
        
        return render(request, self.template_name, context)
    
    def post(self, request, appointment_id=None):
        # Ensure the user is a doctor
        if request.user.role != 'DOCTOR':
            messages.error(request, 'Access denied. Only doctors can create prescriptions.')
            return redirect('dashboard:main')
        
        # Get the doctor profile
        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            messages.error(request, 'Doctor profile not found.')
            return redirect('dashboard:main')
        
        try:
            # Get form data
            patient_id = request.POST.get('patient_id')
            diagnosis = request.POST.get('diagnosis', '')
            symptoms = request.POST.get('symptoms', '')
            notes = request.POST.get('notes', '')
            
            # Get patient
            from apps.patients.models import Patient
            patient = Patient.objects.get(id=patient_id)
            
            # Get appointment if provided
            appointment = None
            if appointment_id:
                from apps.appointments.models import Appointment
                appointment = Appointment.objects.get(
                    id=appointment_id,
                    doctor=doctor
                )
            
            # Create prescription
            from apps.pharmacy.models import Prescription, PrescriptionItem
            prescription = Prescription.objects.create(
                hospital=request.user.hospital,
                patient=patient,
                doctor=doctor,
                appointment=appointment,
                diagnosis=diagnosis,
                symptoms=symptoms,
                notes=notes,
                created_by=request.user
            )
            
            # Add prescription items
            medication_ids = request.POST.getlist('medication_id[]')
            dosages = request.POST.getlist('dosage[]')
            frequencies = request.POST.getlist('frequency[]')
            durations = request.POST.getlist('duration[]')
            quantities = request.POST.getlist('quantity[]')
            instructions = request.POST.getlist('instructions[]')
            
            for i, med_id in enumerate(medication_ids):
                if med_id:  # Skip empty medication selections
                    from apps.pharmacy.models import Medicine
                    medicine = Medicine.objects.get(id=med_id)
                    
                    PrescriptionItem.objects.create(
                        prescription=prescription,
                        medicine=medicine,
                        dosage=dosages[i] if i < len(dosages) else '',
                        frequency=frequencies[i] if i < len(frequencies) else '',
                        duration=durations[i] if i < len(durations) else '',
                        quantity_prescribed=int(quantities[i]) if i < len(quantities) and quantities[i] else 1,
                        instructions=instructions[i] if i < len(instructions) else '',
                        unit_price=medicine.selling_price,  # Use medicine's selling price
                    )
            
            messages.success(request, f'Prescription {prescription.prescription_number} created successfully!')
            return redirect('doctors:prescription_detail', pk=prescription.id)
            
        except Exception as e:
            messages.error(request, f'Error creating prescription: {str(e)}')
            return self.get(request, appointment_id)


class PrescriptionDetailView(LoginRequiredMixin, DetailView):
    """View prescription details - doctor only sees their own prescriptions"""
    template_name = 'doctors/prescription_detail.html'
    context_object_name = 'prescription'
    
    def get_object(self):
        # Ensure the user is a doctor
        if self.request.user.role != 'DOCTOR':
            return None
        
        # Get the doctor profile
        try:
            doctor = Doctor.objects.get(user=self.request.user)
        except Doctor.DoesNotExist:
            return None
        
        # Get prescription - ensure it belongs to this doctor
        from apps.pharmacy.models import Prescription
        try:
            prescription = Prescription.objects.get(
                id=self.kwargs['pk'],
                doctor=doctor
            )
            return prescription
        except Prescription.DoesNotExist:
            return None
    
    def get(self, request, *args, **kwargs):
        prescription = self.get_object()
        if not prescription:
            messages.error(request, 'Prescription not found or access denied.')
            return redirect('doctors:doctor_prescriptions')
        
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get prescription items
        prescription = self.get_object()
        if prescription:
            context['prescription_items'] = prescription.items.all().select_related('medicine')
        
        return context