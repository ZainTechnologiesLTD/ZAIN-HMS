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
from .models import Doctor
from apps.core.mixins import SafeMixin, UnifiedSystemMixin
from apps.core.permissions import audit_action, get_client_ip
from .forms import DoctorForm, DoctorSearchForm
import logging

# Setup security logger for audit trail
security_logger = logging.getLogger('security')


class DoctorListView(SafeMixin, ListView):
    """List all doctors with hospital-specific database routing"""
    model = Doctor
    template_name = 'doctors/doctor_list.html'
    context_object_name = 'doctors'
    paginate_by = 20
    required_roles = ['admin', 'receptionist', 'doctor', 'nurse']
        # tenant_filter_field removed for unified single-DB mode; SafeMixin will handle tenant filtering if needed

    def get_queryset(self):
        # Get the correct database for the hospital
        if self.request.user.is_anonymous:
            # Handle anonymous users - redirect to login will be handled by SafeMixin
            return Doctor.objects.none()
        
        hospital = getattr(self.request, 'hospital', None) or getattr(self.request.user, 'hospital', None)
        
        # Query doctors from the hospital-specific database
        base_queryset = Doctor.objects.filter(is_active=True)
        
        # Search functionality
        search = self.request.GET.get('q')
        if search:
            base_queryset = base_queryset.filter(
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
            base_queryset = base_queryset.filter(specialization=specialization)

        return base_queryset.order_by('first_name', 'last_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = DoctorSearchForm(self.request.GET)
        
        # Handle anonymous users
        if self.request.user.is_anonymous:
            context['total_doctors'] = 0
            context['specializations'] = []
            return context
            
        # Get the correct database for the hospital
        hospital = getattr(self.request, 'hospital', None) or getattr(self.request.user, 'hospital', None)
        
        # Use hospital-specific database for context data
        base_queryset = Doctor.objects.filter(is_active=True)
        context['total_doctors'] = base_queryset.count()
        context['specializations'] = base_queryset.values_list('specialization', flat=True).distinct()
        
        # Add user information for each doctor in the context
        for doctor in context['doctors']:
            # Check if doctor has a user and get user info from hospital database
            if doctor.user_id:
                try:
                    user = User.objects.get(pk=doctor.user_id)
                    doctor.cached_user = user  # Cache the user for template access (no underscore)
                except User.DoesNotExist:
                    doctor.cached_user = None
            else:
                doctor.cached_user = None
        
        return context


class DoctorDetailView(SafeMixin, DetailView):
    """View individual doctor details with hospital-specific database routing"""
    model = Doctor
    template_name = 'doctors/doctor_detail.html'
    context_object_name = 'doctor'
    required_roles = ['admin', 'receptionist', 'doctor', 'nurse']
    # tenant_filter_field removed for unified single-DB mode
    
    def get_queryset(self):
        # Get the correct database for the hospital
        if self.request.user.is_anonymous:
            # Handle anonymous users - redirect to login will be handled by SafeMixin
            return Doctor.objects.none()
            
        hospital = getattr(self.request, 'hospital', None) or getattr(self.request.user, 'hospital', None)# 
        hospital_db = f"hospital_{hospital.subdomain}" if hospital else 'default'
        
        # Query from hospital-specific database
        return Doctor.objects.all()


class DoctorCreateView(SafeMixin, CreateView):
    """Create new doctor with hospital-specific database routing"""
    model = Doctor
    form_class = DoctorForm
    template_name = 'doctors/doctor_form.html'
    success_url = reverse_lazy('doctors:doctor_list')
    required_roles = ['admin']
    # tenant_filter_field removed for unified single-DB mode

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add New Doctor'
        context['submit_text'] = 'Add Doctor'
        return context

    def form_valid(self, form):
        try:
            # Get hospital context from request
            hospital = getattr(self.request, 'hospital', None) or self.request.user.hospital
            
            # Create the doctor instance without saving
            doctor = form.save(commit=False)
            doctor.hospital = hospital
            
            # Check if user account should be created
            create_account = form.cleaned_data.get('create_user_account', True)
            
            if create_account:
                # Get username from form (if provided) or fallback to email
                username = form.cleaned_data.get('username')
                if not username:
                    username = doctor.email  # Fallback to email as username
                
                # Get password from form (if provided) or use default
                password = form.cleaned_data.get('password')
                if not password:
                    password = 'Asdf@1234'  # Use standard password
                
                # Prepare user data for account creation
                user_data = {
                    'first_name': doctor.first_name,
                    'last_name': doctor.last_name,
                    'email': doctor.email,
                    'username': username,  # Use the provided username or email
                    'phone_number': doctor.phone_number,
                    'user_type': 'doctor',
                    'hospital': hospital,
                }
                
                # Use UserManagementService to create the user account in hospital database
                user_service = UserManagementService()
                
                # Create user in hospital database using the correct manager
                # Create user using the default database/manager
                user = User.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    password=password,
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name']
                )
                
                # Update additional user fields after creation
                user.phone = doctor.phone_number  # Use 'phone' field from CustomUser model
                user.role = 'DOCTOR'  # Use 'role' field instead of 'user_type'
                user.hospital = hospital
                user.save()
                
                # Link the doctor to the created user
                doctor.user = user
                
                messages.success(
                    self.request,
                    f"Doctor {doctor.first_name} {doctor.last_name} has been created successfully! "
                    f"Login credentials - Username: {user.username}, Password: {password}"
                )
            else:
                # No user account created
                messages.success(
                    self.request,
                    f"Doctor {doctor.first_name} {doctor.last_name} has been created successfully! "
                    f"(No user account created)"
                )
            
            # Save doctor (single-database)
            doctor.save()
            
            return redirect(self.success_url)
            
        except Exception as e:
            messages.error(
                self.request,
                f"Error creating doctor account: {str(e)}"
            )
            return self.form_invalid(form)


class DoctorUpdateView(SafeMixin, UpdateView):
    """Update existing doctor with hospital-specific database routing"""
    model = Doctor
    form_class = DoctorForm
    template_name = 'doctors/doctor_form.html'
    required_roles = ['admin']
    # tenant_filter_field removed for unified single-DB mode
    
    def get_queryset(self):
        # Get the correct database for the hospital
        if self.request.user.is_anonymous:
            # Handle anonymous users - redirect to login will be handled by SafeMixin
            from django.db import models
            return Doctor.objects.none()
            
        hospital = getattr(self.request, 'hospital', None) or getattr(self.request.user, 'hospital', None)# 
        hospital_db = f"hospital_{hospital.subdomain}" if hospital else 'default'
        
        # Query from hospital-specific database
        return Doctor.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Update Doctor: {self.object.get_full_name()}'
        context['submit_text'] = 'Update Doctor'
        return context

    def form_valid(self, form):
        try:
            # Get hospital context for database routing
            if self.request.user.is_anonymous:
                messages.error(self.request, "Authentication required")
                return self.form_invalid(form)
                
            hospital = getattr(self.request, 'hospital', None) or getattr(self.request.user, 'hospital', None)
            
            # Get the original doctor instance from the hospital database
            original_doctor = self.get_object()
            
            # Create a new doctor instance with form data
            doctor = form.save(commit=False)
            doctor.pk = original_doctor.pk  # Ensure we're updating the same record
            
            # Check for unique constraint conflicts within the hospital database
            existing_email = Doctor.objects.exclude(pk=doctor.pk).filter(email=doctor.email).first()
            if existing_email:
                form.add_error('email', 'A doctor with this email already exists.')
                return self.form_invalid(form)
                
            existing_license = Doctor.objects.exclude(pk=doctor.pk).filter(license_number=doctor.license_number).first()
            if existing_license:
                form.add_error('license_number', 'A doctor with this license number already exists.')
                return self.form_invalid(form)
            
            # Preserve the original user relationship by using the user_id
            if original_doctor.user_id:
                doctor.user_id = original_doctor.user_id
            
            # Save the doctor (single-database)
            doctor.save()
            
            messages.success(self.request, 'Doctor information updated successfully!')
            
            # Redirect to success URL without calling super().form_valid()
            return redirect(self.get_success_url())
            
        except Exception as e:
            messages.error(
                self.request,
                f"Error updating doctor: {str(e)}"
            )
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('doctors:doctor_detail', kwargs={'pk': self.object.pk})


class DoctorDeleteView(SafeMixin, DeleteView):
    """Delete doctor with hospital-specific database routing"""
    model = Doctor
    template_name = 'doctors/doctor_confirm_delete.html'
    success_url = reverse_lazy('doctors:doctor_list')
    required_roles = ['admin']
    # tenant_filter_field removed for unified single-DB mode
    
    def get_queryset(self):
        # Get the correct database for the hospital
        if self.request.user.is_anonymous:
            # Handle anonymous users - redirect to login will be handled by SafeMixin
            return Doctor.objects.none()
            
        hospital = getattr(self.request, 'hospital', None) or getattr(self.request.user, 'hospital', None)# 
        hospital_db = f"hospital_{hospital.subdomain}" if hospital else 'default'
        
        # Query from hospital-specific database
        return Doctor.objects.all()

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        
        # Get hospital context for database routing
        if request.user.is_anonymous:
            messages.error(request, "Authentication required")
            return redirect('doctors:doctor_list')
        
        hospital = getattr(request, 'hospital', None) or getattr(request.user, 'hospital', None)
        
        # Validate confirmation input
        confirm_name = request.POST.get('confirm_name', '').strip()
        expected_name = self.object.get_full_name()
        
        if confirm_name != expected_name:
            messages.error(request, f"Please type the exact doctor name '{expected_name}' to confirm deletion.")
            return self.get(request, *args, **kwargs)  # Return to confirmation page

        # Soft delete - just mark as inactive instead of hard delete
        doctor_name = self.object.get_full_name()
        doctor_id = self.object.id
        
        self.object.is_active = False
        self.object.save()

        # Audit log the doctor deletion/deactivation
        security_logger.info(
            f"DOCTOR_DELETE: User {request.user.username} (ID: {request.user.id}) "
            f"deactivated doctor '{doctor_name}' (ID: {doctor_id}) "
            f"from IP {get_client_ip(request)} at {timezone.now()}"
        )

        messages.success(request, f'Doctor {doctor_name} has been deactivated.')
        return redirect(success_url)


class DoctorBulkActionView(SafeMixin, View):
    """Handle bulk actions for doctors"""
    required_roles = ['admin']
    
    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        selected_ids = request.POST.getlist('selected_doctors')
        
        if not selected_ids:
            messages.error(request, 'No doctors selected.')
            return redirect('doctors:doctor_list')
        
        # Get hospital context for database routing
        hospital = getattr(request, 'hospital', None) or getattr(request.user, 'hospital', None)# 
        hospital_db = f"hospital_{hospital.subdomain}" if hospital else 'default'
        
        try:
            doctors = Doctor.objects.filter(id__in=selected_ids)
            count = doctors.count()
            
            if action == 'activate':
                doctors.update(is_active=True)
                messages.success(request, f'Successfully activated {count} doctor(s).')
            elif action == 'deactivate':
                doctors.update(is_active=False)
                messages.success(request, f'Successfully deactivated {count} doctor(s).')
            elif action == 'delete':
                # Soft delete - mark as inactive
                doctors.update(is_active=False)
                messages.success(request, f'Successfully deleted {count} doctor(s).')
            else:
                messages.error(request, 'Invalid action.')
        except Exception as e:
            messages.error(request, f'Error performing bulk action: {str(e)}')
        
        return redirect('doctors:doctor_list')


class DoctorDashboardView(SafeMixin, View):
    """Doctor dashboard view - placeholder for now"""
    required_roles = ['doctor']
    template_name = 'doctors/doctor_dashboard.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {
            'title': 'Doctor Dashboard',
            'message': 'Welcome to the Doctor Dashboard'
        })


class DoctorAppointmentsView(SafeMixin, ListView):
    """Doctor's appointments view - shows only doctor's own appointments"""
    template_name = 'doctors/doctor_appointments.html'
    required_roles = ['doctor']
    context_object_name = 'appointments'
    paginate_by = 20

    def get_queryset(self):
        """Get appointments for the logged-in doctor only"""
        from apps.appointments.models import Appointment
        from apps.doctors.models import Doctor

        try:
            # Get the doctor instance for the logged-in user
            doctor_instance = Doctor.objects.get(user=self.request.user)
            
            # Filter appointments by this doctor only
            appointments = Appointment.objects.filter(
                doctor=doctor_instance
            ).select_related('patient', 'doctor', 'created_by').order_by('-appointment_date', '-appointment_time')
            
            return appointments
            
        except Doctor.DoesNotExist:
            # If no doctor profile exists, return empty queryset
            return Appointment.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add statistics for the doctor's appointments
        queryset = self.get_queryset()
        from django.utils import timezone
        today = timezone.now().date()
        
        context['stats'] = {
            'total': queryset.count(),
            'today': queryset.filter(appointment_date=today).count(),
            'scheduled': queryset.filter(status='SCHEDULED').count(),
            'completed': queryset.filter(status='COMPLETED').count(),
        }
        
        return context


class DoctorPrescriptionsView(SafeMixin, ListView):
    """Doctor's prescriptions view - placeholder for now"""
    template_name = 'doctors/doctor_prescriptions.html'
    required_roles = ['doctor']
    context_object_name = 'prescriptions'

    def get_queryset(self):
        return []  # Placeholder - return empty list for now


class CreatePrescriptionView(SafeMixin, View):
    """Create prescription view - placeholder for now"""
    required_roles = ['doctor']
    template_name = 'doctors/create_prescription.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {
            'title': 'Create Prescription',
            'message': 'Prescription creation form will be here'
        })


class PrescriptionDetailView(SafeMixin, View):
    """Prescription detail view - placeholder for now"""
    required_roles = ['doctor', 'nurse', 'admin']
    template_name = 'doctors/prescription_detail.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {
            'title': 'Prescription Detail',
            'message': 'Prescription details will be here'
        })


class CreateUserForDoctorView(SafeMixin, View):
    """Create user account for existing doctor - placeholder for now"""
    required_roles = ['admin']
    template_name = 'doctors/create_user_for_doctor.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {
            'title': 'Create User for Doctor',
            'message': 'User creation form will be here'
        })


class LinkDoctorUserView(SafeMixin, View):
    """Link existing user to doctor - placeholder for now"""
    required_roles = ['admin']
    template_name = 'doctors/link_doctor_user.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {
            'title': 'Link User to Doctor',
            'message': 'User linking form will be here'
        })


class DoctorsWithoutUsersView(SafeMixin, ListView):
    """List doctors without user accounts - placeholder for now"""
    template_name = 'doctors/doctors_without_users.html'
    required_roles = ['admin']
    context_object_name = 'doctors'

    def get_queryset(self):
        return []  # Placeholder - return empty list for now


@login_required
def unlink_doctor_user(request, pk):
    """Unlink user from doctor - placeholder function"""
    messages.success(request, 'User unlinked from doctor (placeholder)')
    return redirect('doctors:doctor_list')
