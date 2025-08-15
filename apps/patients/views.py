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
from .models import Patient, PatientDocument, PatientNote, PatientVitals
from .forms import (
    PatientForm, QuickPatientForm, PatientSearchForm,
    PatientDocumentForm, PatientNoteForm, PatientVitalsForm
)

class PatientListView(LoginRequiredMixin, ListView):
    """List all patients with search and filtering"""
    model = Patient
    template_name = 'patients/patient_list.html'
    context_object_name = 'patients'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Patient.objects.filter(
            hospital=self.request.user.hospital,
            is_active=True
        ).select_related('registered_by')
        
        # Search functionality
        search = self.request.GET.get('search')
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
        context['total_patients'] = Patient.objects.filter(
            hospital=self.request.user.hospital,
            is_active=True
        ).count()
        context['vip_patients'] = Patient.objects.filter(
            hospital=self.request.user.hospital,
            is_active=True,
            is_vip=True
        ).count()
        return context


class PatientDetailView(LoginRequiredMixin, DetailView):
    """Detailed patient view with medical history"""
    model = Patient
    template_name = 'patients/patient_detail.html'
    context_object_name = 'patient'
    
    def get_queryset(self):
        return Patient.objects.filter(hospital=self.request.user.hospital)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        patient = self.object
        
        # Get related data
        context['documents'] = patient.documents.all()[:10]
        context['notes'] = patient.notes.all()[:10]
        context['vitals'] = patient.vitals.all()[:5]
        context['appointments'] = patient.appointments.all()[:10]
        
        # Forms for adding data
        context['document_form'] = PatientDocumentForm()
        context['note_form'] = PatientNoteForm()
        context['vitals_form'] = PatientVitalsForm()
        
        return context


class PatientCreateView(LoginRequiredMixin, CreateView):
    """Create new patient"""
    model = Patient
    form_class = PatientForm
    template_name = 'patients/patient_form.html'
    
    def form_valid(self, form):
        form.instance.hospital = self.request.user.hospital
        form.instance.registered_by = self.request.user
        messages.success(self.request, 'Patient registered successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('patients:detail', kwargs={'pk': self.object.pk})


class PatientUpdateView(LoginRequiredMixin, UpdateView):
    """Update patient information"""
    model = Patient
    form_class = PatientForm
    template_name = 'patients/patient_form.html'
    
    def get_queryset(self):
        return Patient.objects.filter(hospital=self.request.user.hospital)
    
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
            patient.hospital = request.user.hospital
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
        hospital=request.user.hospital,
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
def add_patient_document(request, patient_id):
    """Add document to patient"""
    patient = get_object_or_404(Patient, id=patient_id, hospital=request.user.hospital)
    
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
    patient = get_object_or_404(Patient, id=patient_id, hospital=request.user.hospital)
    
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
    patient = get_object_or_404(Patient, id=patient_id, hospital=request.user.hospital)
    
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


class PatientDeleteView(LoginRequiredMixin, DeleteView):
    """Soft delete patient (set inactive)"""
    model = Patient
    template_name = 'patients/patient_confirm_delete.html'
    success_url = reverse_lazy('patients:list')
    
    def get_queryset(self):
        return Patient.objects.filter(hospital=self.request.user.hospital)
    
    def delete(self, request, *args, **kwargs):
        # Soft delete - set inactive instead of deleting
        self.object = self.get_object()
        self.object.is_active = False
        self.object.save()
        messages.success(request, 'Patient record has been deactivated.')
        return redirect(self.success_url)