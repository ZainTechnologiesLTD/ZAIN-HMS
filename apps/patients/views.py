# apps/patients/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.utils import timezone
import logging
from .models import Patient, PatientDocument, PatientNote, PatientVitals
from .forms import (
    PatientForm, QuickPatientForm, PatientSearchForm,
    PatientDocumentForm, PatientNoteForm, PatientVitalsForm
)
from apps.accounts.services import UserManagementService
from apps.core.mixins import TenantSafeMixin, RequireHospitalSelectionMixin, require_hospital_selection
# from tenants.permissions import  # Temporarily commented TenantFilterMixin

logger = logging.getLogger(__name__)

class PatientListView(TenantSafeMixin, ListView):  # ListView): # Temporarily simplified
    """List all patients with search and filtering"""
    model = Patient
    template_name = 'patients/patient_list.html'
    context_object_name = 'patients'
    paginate_by = 20
    required_roles = ['admin', 'doctor', 'nurse', 'receptionist']
    
    def get_queryset(self):
        # Use TenantFilterMixin to get tenant-filtered queryset
        queryset = self.filter_by_tenant(Patient.objects.filter(is_active=True)).select_related('registered_by')
        
        # Search functionality
        search = self.request.GET.get('q')  # Fixed: changed from 'search' to 'q'
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(patient_id__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search)
            )
        
        # Filter by gender
        gender = self.request.GET.get('gender')
        if gender:
            queryset = queryset.filter(gender=gender)
            
        # Filter by blood group
        blood_group = self.request.GET.get('blood_group')
        if blood_group:
            queryset = queryset.filter(blood_group=blood_group)
            
    # Filter VIP patients
        is_vip = self.request.GET.get('is_vip')
        if is_vip:
            queryset = queryset.filter(is_vip=True)
        return queryset.order_by('-registration_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = PatientSearchForm(self.request.GET)
        
        # Use the tenant-safe queryset helper
        patient_queryset = self.get_tenant_safe_queryset(Patient)
        
        context['total_patients'] = patient_queryset.filter(is_active=True).count()
        context['vip_patients'] = patient_queryset.filter(
            is_active=True,
            is_vip=True
        ).count()
        
        # Add flag to indicate if no hospital is selected
        context['no_hospital_selected'] = self.get_current_tenant() is None
        
        return context


class PatientDetailView(RequireHospitalSelectionMixin, LoginRequiredMixin, DetailView):
    """Detailed patient view with medical history"""
    model = Patient
    template_name = 'patients/patient_detail.html'
    context_object_name = 'patient'
    
    def get_queryset(self):
        # Route-based isolation; no explicit tenant field required
        return Patient.objects.all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        patient = self.object
        
        # Get related data using correct related_names
        context['documents'] = patient.documents.all()[:10]
        context['patient_notes'] = patient.patient_notes.all()[:10]  # Fixed: use patient_notes instead of notes
        context['vitals'] = patient.vitals.all()[:5]
        context['appointments'] = patient.appointments.all()[:10]
        
        # Forms for adding data
        context['document_form'] = PatientDocumentForm()
        context['note_form'] = PatientNoteForm()
        context['vitals_form'] = PatientVitalsForm()
        
        return context


class PatientCreateView(RequireHospitalSelectionMixin, CreateView):  # CreateView): # Temporarily simplified
    """Create new patient"""
    model = Patient
    form_class = PatientForm
    template_name = 'patients/patient_form.html'
    required_roles = ['admin', 'receptionist', 'doctor', 'nurse']
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Explicitly set that this is a create operation
        context['is_create'] = True
        return context
    
    def form_valid(self, form):
        try:
            # Hospital selection is enforced by RequireHospitalSelectionMixin
            # Check selected hospital from session
            selected_hospital_code = self.request.session.get('selected_hospital_code')
            if not selected_hospital_code:
                messages.error(self.request, 'Hospital selection required. Please select a hospital first.')
                return self.form_invalid(form)
            
            patient = form.save(commit=False)
            
            # Set tenant field if the model has it (defensive coding)
            if hasattr(patient, 'tenant'):
                tenant = getattr(self.request, 'tenant', None)
                if tenant:
                    patient.tenant = tenant
                else:
                    # If no tenant object available, log and continue (DB router will handle isolation)
                    logger.warning(f"PATIENT_CREATE: No tenant object available for hospital {selected_hospital_code}")
            
            patient.registered_by = self.request.user
            
            # Create user account for patient if email is provided
            if patient.email:
                logger.info(f"PATIENT_CREATE: About to create user account for {patient.email}")
                try:
                    user = UserManagementService.create_user_account(
                        email=patient.email,
                        first_name=patient.first_name,
                        last_name=patient.last_name,
                        role='PATIENT',
                        tenant=getattr(self.request, 'tenant', None),
                        created_by=self.request.user,
                        additional_data={
                            'phone': patient.phone,
                            'date_of_birth': patient.date_of_birth,
                            'gender': patient.gender,
                            'blood_group': patient.blood_group,
                            'address': f"{patient.address_line1}, {patient.city}, {patient.state}",
                        }
                    )
                    logger.info(f"PATIENT_CREATE: User account created successfully: {user.username}")
                    # Note: Patient model doesn't have direct user field
                    # User account is created but stored separately
                except Exception as user_error:
                    logger.error(f"PATIENT_CREATE: Error in UserManagementService: {str(user_error)}")
                    raise user_error
            
            # Save the patient
            patient.save()
            self.object = patient
            
            if patient.email:
                messages.success(
                    self.request,
                    f'Patient {patient.get_full_name()} registered successfully! '
                    f'Login credentials have been sent to {patient.email}.'
                )
            else:
                messages.success(self.request, 'Patient registered successfully!')
                
            return redirect(self.get_success_url())
            
        except Exception as e:
            logger.error(f"PATIENT_CREATE: General error: {str(e)}")
            messages.error(
                self.request,
                f'Error creating patient account: {str(e)}'
            )
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse('patients:detail', kwargs={'pk': self.object.pk})


class PatientUpdateView(RequireHospitalSelectionMixin, LoginRequiredMixin, UpdateView):
    """Update patient information"""
    model = Patient
    form_class = PatientForm
    template_name = 'patients/patient_form.html'
    
    def get_queryset(self):
        # Route-based isolation; no explicit tenant filter
        return Patient.objects.all()
    
    def form_valid(self, form):
        messages.success(self.request, 'Patient information updated successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('patients:detail', kwargs={'pk': self.object.pk})


@login_required
def quick_patient_register(request):
    """Quick patient registration via HTMX"""
    if request.method == 'POST':
        form = QuickPatientForm(request.POST)
        if form.is_valid():
            patient = form.save(commit=False)
            # Use tenant from middleware (set by HospitalSelectionRequiredMiddleware)
            tenant = getattr(request, 'tenant', request.user.tenant)
            patient.tenant = tenant
            patient.registered_by = request.user
            patient.save()
            
            if request.headers.get('HX-Request'):
                return JsonResponse({
                    'success': True,
                    'message': 'Patient registered successfully!',
                    'patient_id': str(patient.id),
                    'patient_name': patient.get_full_name()
                })
            else:
                messages.success(request, 'Patient registered successfully!')
                return redirect('patients:detail', pk=patient.pk)
    else:
        form = QuickPatientForm()
    
    return render(request, 'patients/quick_register.html', {'form': form})


@login_required
def patient_search_api(request):
    """API endpoint for patient search (for autocomplete)"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'patients': []})
    
    patients = Patient.objects.filter(
        is_active=True
    ).filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(patient_id__icontains=query) |
        Q(phone__icontains=query)
    )[:10]
    
    patient_data = []
    for patient in patients:
        patient_data.append({
            'id': str(patient.id),
            'patient_id': patient.patient_id,
            'name': patient.get_full_name(),
            'phone': patient.phone,
            'age': patient.get_age(),
            'gender': patient.get_gender_display(),
        })
    
    return JsonResponse({'patients': patient_data})


@login_required
@require_hospital_selection
def add_patient_document(request, patient_id):
    """Add document to patient"""
    # Use tenant from middleware (set by HospitalSelectionRequiredMiddleware)
    tenant = getattr(request, 'tenant', request.user.tenant)
    patient = get_object_or_404(Patient, id=patient_id, tenant=tenant)
    
    if request.method == 'POST':
        form = PatientDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.patient = patient
            document.uploaded_by = request.user
            document.save()
            
            messages.success(request, 'Document uploaded successfully!')
            return redirect('patients:detail', pk=patient.pk)
    
    return redirect('patients:detail', pk=patient.pk)


@login_required
@require_hospital_selection
def add_patient_note(request, patient_id):
    """Add note to patient"""
    # Use tenant from middleware (set by HospitalSelectionRequiredMiddleware)
    tenant = getattr(request, 'tenant', request.user.tenant)
    patient = get_object_or_404(Patient, id=patient_id, tenant=tenant)
    
    if request.method == 'POST':
        form = PatientNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.patient = patient
            note.created_by = request.user
            note.save()
            
            if request.headers.get('HX-Request'):
                return render(request, 'patients/partials/note_item.html', {
                    'note': note
                })
            
            messages.success(request, 'Note added successfully!')
            return redirect('patients:detail', pk=patient.pk)
    
    return redirect('patients:detail', pk=patient.pk)


@login_required
@require_hospital_selection
def add_patient_vitals(request, patient_id):
    """Record patient vitals"""
    # Use tenant from middleware (set by HospitalSelectionRequiredMiddleware)
    tenant = getattr(request, 'tenant', request.user.tenant)
    patient = get_object_or_404(Patient, id=patient_id, tenant=tenant)
    
    if request.method == 'POST':
        form = PatientVitalsForm(request.POST)
        if form.is_valid():
            vitals = form.save(commit=False)
            vitals.patient = patient
            vitals.recorded_by = request.user
            vitals.save()
            
            # Update patient's last visit
            patient.last_visit = timezone.now()
            patient.save(update_fields=['last_visit'])
            
            messages.success(request, 'Vitals recorded successfully!')
            return redirect('patients:detail', pk=patient.pk)
    
    return redirect('patients:detail', pk=patient.pk)


class PatientDeleteView(RequireHospitalSelectionMixin, LoginRequiredMixin, DeleteView):
    """Soft delete patient (set inactive)"""
    model = Patient
    template_name = 'patients/patient_confirm_delete.html'
    success_url = reverse_lazy('patients:list')
    
    def get_queryset(self):
        # Route-based isolation; no explicit tenant filter
        return Patient.objects.all()
    
    def delete(self, request, *args, **kwargs):
        # Soft delete - set inactive instead of deleting
        self.object = self.get_object()
        self.object.is_active = False
        self.object.save()
        messages.success(request, 'Patient record has been deactivated.')
        return redirect(self.success_url)
