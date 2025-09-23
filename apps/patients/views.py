# apps/patients/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
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
from apps.core.mixins import SafeMixin, UnifiedSystemMixin
from apps.core.permissions import (
    PatientAccessMixin, SecureViewMixin, audit_action, 
    patient_access_required, get_client_ip
)
# 
logger = logging.getLogger(__name__)
security_logger = logging.getLogger('security')  # For audit trail


class PatientListView(SecureViewMixin, PatientAccessMixin, SafeMixin, ListView):
    """List all patients with search and filtering - SECURE"""
    model = Patient
    template_name = 'patients/patient_list.html'  # Standard template name
    context_object_name = 'patients'
    paginate_by = 25  # Increased for better enterprise experience
    required_roles = ['admin', 'doctor', 'nurse', 'receptionist']
        # tenant_filter_field removed for unified single-DB mode
    
    def get_queryset(self):
        """Get patients for unified ZAIN HMS system"""
        # ZAIN HMS unified system - all patients in single database
        queryset = Patient.objects.filter(is_active=True).select_related('registered_by')
        
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
        
        # ZAIN HMS unified system - all patients in single database
        patient_queryset = Patient.objects.filter(is_active=True)
        
        context['total_patients'] = patient_queryset.count()
        context['vip_patients'] = patient_queryset.filter(is_vip=True).count()
        
        # ZAIN HMS unified system - no hospital selection needed
        context['no_hospital_selected'] = False
        
        return context
    
    def get(self, request, *args, **kwargs):
        """Handle HTMX and regular GET requests"""
        response = super().get(request, *args, **kwargs)
        
        # For HTMX requests, return only the table container
        if request.headers.get('HX-Request'):
            context = self.get_context_data()
            return render(request, 'patients/partials/patient_table.html', context)
            
        return response


class PatientDetailView(UnifiedSystemMixin, LoginRequiredMixin, DetailView):
    """Detailed patient view with medical history"""
    model = Patient
    template_name = 'patients/patient_detail.html'
    context_object_name = 'patient'
    
    def get_queryset(self):
        """Get patients for unified ZAIN HMS system"""
        # ZAIN HMS unified system - all patients in single database
        return Patient.objects.filter(is_active=True)
    
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


class PatientCreateView(UnifiedSystemMixin, CreateView):  # CreateView): # Temporarily simplified
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
            # ZAIN HMS unified system - no hospital selection needed
            patient = form.save(commit=False)
            
            # ZAIN HMS unified system - set user fields
            patient.registered_by = self.request.user
            patient.created_by = self.request.user
            patient.updated_by = self.request.user
            
            # Create user account for patient if email is provided
            if patient.email:
                logger.info(f"PATIENT_CREATE: User account can be created separately if needed for {patient.email}")
            
            # Save the patient to ZAIN HMS unified database
            patient.save()
            self.object = patient
            
            if patient.email and 'user_error' not in locals():
                messages.success(
                    self.request,
                    f'Patient {patient.get_full_name()} registered successfully! '
                    f'Login credentials have been sent to {patient.email}.'
                )
            else:
                messages.success(self.request, f'Patient {patient.get_full_name()} registered successfully!')
                
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


class PatientUpdateView(UnifiedSystemMixin, LoginRequiredMixin, UpdateView):
    """Update patient information"""
    model = Patient
    form_class = PatientForm
    template_name = 'patients/patient_form.html'
    
    def get_queryset(self):
        """Get patients for unified ZAIN HMS system"""
        # ZAIN HMS unified system - all patients in single database
        return Patient.objects.filter(is_active=True)
    
    def form_valid(self, form):
        # Set updated_by field
        form.instance.updated_by = self.request.user
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
            # Single hospital system - no tenant needed
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
@login_required
def add_patient_document(request, patient_id):
    """Add document to patient"""
    # ZAIN HMS unified system - no hospital selection needed
    try:
        patient = Patient.objects.get(id=patient_id, is_active=True)
    except Patient.DoesNotExist:
        messages.error(request, 'Patient not found.')
        return redirect('patients:list')
    
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
def add_patient_note(request, patient_id):
    """Add note to patient"""
    # ZAIN HMS unified system - no hospital selection needed
    try:
        patient = Patient.objects.get(id=patient_id, is_active=True)
    except Patient.DoesNotExist:
        messages.error(request, 'Patient not found.')
        return redirect('patients:list')
    
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
def add_patient_vitals(request, patient_id):
    """Record patient vitals"""
    # ZAIN HMS unified system - no hospital selection needed
    try:
        patient = Patient.objects.get(id=patient_id, is_active=True)
    except Patient.DoesNotExist:
        messages.error(request, 'Patient not found.')
        return redirect('patients:list')
    except Patient.DoesNotExist:
        messages.error(request, 'Patient not found.')
        return redirect('patients:list')
    
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


class PatientDeleteView(UnifiedSystemMixin, LoginRequiredMixin, DeleteView):
    """Soft delete patient (set inactive) with AJAX support"""
    model = Patient
    template_name = 'patients/patient_confirm_delete.html'
    success_url = reverse_lazy('patients:list')
    
    def get_queryset(self):
        """Get patients for unified ZAIN HMS system"""
        # ZAIN HMS unified system - all patients in single database
        return Patient.objects.filter(is_active=True)
    
    def delete(self, request, *args, **kwargs):
        # Handle HTMX requests 
        if request.headers.get('HX-Request'):
            try:
                self.object = self.get_object()
                patient_id = self.object.patient_id
                patient_name = f"{self.object.first_name} {self.object.last_name}"
                
                self.object.is_active = False
                self.object.save()
                
                # Audit log the patient deletion/deactivation
                security_logger.info(
                    f"PATIENT_DELETE: User {request.user.username} (ID: {request.user.id}) "
                    f"deactivated patient '{patient_name}' (ID: {patient_id}) "
                    f"from IP {get_client_ip(request)} at {timezone.now()}"
                )
                
                logger.info(f"Patient {self.object.patient_id} deactivated via HTMX by {request.user.username}")
                return HttpResponse(status=200)  # Success response for HTMX
            except Exception as e:
                logger.error(f"Error deactivating patient via HTMX: {str(e)}")
                return HttpResponse(status=500)  # Error response for HTMX
        
        # Handle AJAX requests (legacy)
        if request.headers.get('Content-Type') == 'application/json':
            try:
                self.object = self.get_object()
                patient_id = self.object.patient_id
                patient_name = f"{self.object.first_name} {self.object.last_name}"
                
                self.object.is_active = False
                self.object.save()
                
                # Audit log the patient deletion/deactivation
                security_logger.info(
                    f"PATIENT_DELETE: User {request.user.username} (ID: {request.user.id}) "
                    f"deactivated patient '{patient_name}' (ID: {patient_id}) "
                    f"from IP {get_client_ip(request)} at {timezone.now()}"
                )
                
                return JsonResponse({
                    'success': True,
                    'message': 'Patient record has been deactivated successfully.'
                })
            except Exception as e:
                logger.error(f"Error deactivating patient {self.object.pk if hasattr(self, 'object') else 'unknown'}: {str(e)}")
                return JsonResponse({
                    'success': False,
                    'message': f'Error deactivating patient: {str(e)}'
                }, status=500)
        
        # Handle regular form submissions (fallback)
        try:
            self.object = self.get_object()
            patient_id = self.object.patient_id
            patient_name = f"{self.object.first_name} {self.object.last_name}"
            
            self.object.is_active = False
            self.object.save()
            
            # Audit log the patient deletion/deactivation
            security_logger.info(
                f"PATIENT_DELETE: User {request.user.username} (ID: {request.user.id}) "
                f"deactivated patient '{patient_name}' (ID: {patient_id}) "
                f"from IP {get_client_ip(request)} at {timezone.now()}"
            )
            
            messages.success(request, 'Patient record has been deactivated successfully.')
            return redirect(self.success_url)
        except Exception as e:
            logger.error(f"Error deactivating patient {self.object.pk if hasattr(self, 'object') else 'unknown'}: {str(e)}")
            messages.error(request, f'Error deactivating patient: {str(e)}')
            return redirect(self.success_url)


class PatientBulkActionView(SafeMixin, LoginRequiredMixin, View):
    """Handle bulk actions for patients with AJAX support"""
    required_roles = ['admin', 'doctor', 'nurse']
    
    def post(self, request, *args, **kwargs):
        # Handle HTMX requests
        if request.headers.get('HX-Request'):
            action = request.POST.get('action')
            selected_ids = request.POST.getlist('patient_ids')
        # Handle JSON requests
        elif request.content_type == 'application/json':
            import json
            data = json.loads(request.body)
            action = data.get('action')
            selected_ids = data.get('selected_patients', [])
        else:
            # Handle form requests
            action = request.POST.get('action')
            selected_ids = request.POST.getlist('selected_patients')
        
        if not selected_ids:
            if request.headers.get('HX-Request'):
                return HttpResponse(status=400)
            elif request.content_type == 'application/json':
                return JsonResponse({'success': False, 'message': 'No patients selected.'})
            else:
                messages.error(request, 'No patients selected.')
                return redirect('patients:list')
        
        # ZAIN HMS unified system - no hospital selection needed
        try:
            patients = Patient.objects.filter(id__in=selected_ids)
            count = patients.count()

            if action == 'activate':
                patients.update(is_active=True)
                message = f'Successfully activated {count} patient(s).'
                success = True
            elif action == 'deactivate':
                patients.update(is_active=False)
                message = f'Successfully deactivated {count} patient(s).'
                success = True
            elif action == 'delete':
                # Soft delete - mark as inactive
                patients.update(is_active=False)
                message = f'Successfully deleted {count} patient(s).'
                success = True
            else:
                message = 'Invalid action.'
                success = False

            # Return appropriate response
            if request.headers.get('HX-Request'):
                if success:
                    return HttpResponse(status=200)
                else:
                    return HttpResponse(status=400)
            elif request.content_type == 'application/json':
                return JsonResponse({
                    'success': success, 
                    'message': message,
                    'count': count if success else 0
                })
            else:
                if success:
                    messages.success(request, message)
                else:
                    messages.error(request, message)

        except Exception as e:
            logger.error(f"Bulk action error: {str(e)}")
            if request.headers.get('HX-Request'):
                return HttpResponse(status=500)
            elif request.content_type == 'application/json':
                return JsonResponse({'success': False, 'message': str(e)})
            else:
                messages.error(request, f'Error performing bulk action: {str(e)}')

        return redirect('patients:list')


class PatientPrintView(SecureViewMixin, PatientAccessMixin, SafeMixin, DetailView):
    """Print patient information - SECURE"""
    model = Patient
    template_name = 'patients/patient_print.html'
    context_object_name = 'patient'
    required_roles = ['admin', 'doctor', 'nurse', 'receptionist']
        # tenant_filter_field removed for unified single-DB mode
    
    def get_queryset(self):
        """Get patients for unified ZAIN HMS system"""
        # ZAIN HMS unified system - all patients in single database
        return Patient.objects.filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # ZAIN HMS unified system - no hospital context needed
        context['hospital'] = {'name': 'ZAIN Hospital Management System'}
        
        # Add current date and time for print header
        context['current_datetime'] = timezone.now()
        
        # Get patient vitals if available
        patient = self.get_object()
        context['latest_vitals'] = patient.vitals.order_by('-recorded_at').first() if hasattr(patient, 'vitals') else None
        
        # Get patient notes (recent ones)
        if hasattr(patient, 'patient_notes'):
            context['recent_notes'] = patient.patient_notes.order_by('-created_at')[:5]
        
        return context

