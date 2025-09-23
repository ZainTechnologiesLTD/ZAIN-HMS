# apps/emr/views.py
"""
Traditional EMR Views and API Views for AJAX Support
"""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, 
    DeleteView, TemplateView, View
)
from django.contrib import messages
from apps.core.mixins import UnifiedSystemMixin
from django.urls import reverse_lazy
from django.db.models import Q
from django.core.paginator import Paginator

from .models import (
    MedicalRecord, VitalSigns, Medication, LabResult,
    ClinicalAlert, ClinicalDecisionSupport
)
from .api_views import (
    AlertDetailAPIView, RecommendationDetailAPIView,
    PatientRiskAPIView, ClinicalMetricsAPIView, AISystemStatusAPIView
)
from apps.patients.models import Patient
# 
logger = logging.getLogger(__name__)


def get_hospital_context(request):
    """Helper function for ZAIN HMS unified system - simplified context"""
    # Return a single hospital marker for compatibility
    return getattr(request, 'hospital', None) or getattr(getattr(request, 'user', None), 'hospital', None)


class EMRDashboardView(TemplateView):
    """
    EMR Dashboard with traditional medical records overview
    """
    template_name = 'emr/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            hospital = get_hospital_context(self.request)
            if not hospital:
                # In unified mode, it's okay if hospital is not set; return empty results
                context.update({
                    'recent_records': [],
                    'recent_vitals': [],
                    'active_medications': 0,
                    'pending_labs': 0,
                })
                return context
            
            # Get recent medical records - use hospital database
            try:
                recent_records = MedicalRecord.objects.filter(
                    patient__hospital=hospital  # Filter by patient's hospital
                ).select_related('patient').order_by('-record_date')[:10]
            except:
                recent_records = []
            
            # Get recent vital signs - use hospital database
            try:
                recent_vitals = VitalSigns.objects.filter(
                    patient__hospital=hospital  # Filter by patient's hospital
                ).select_related('patient').order_by('-recorded_at')[:10]
            except:
                recent_vitals = []
            
            # Get active medications - use hospital database
            try:
                active_medications = Medication.objects.filter(
                    patient__hospital=hospital,
                    status='ACTIVE'
                ).select_related('patient').count()
            except:
                active_medications = 0
            
            # Get pending lab results - use hospital database
            try:
                pending_labs = LabResult.objects.filter(
                    patient__hospital=hospital,
                    status='PENDING'
                ).select_related('patient').count()
            except:
                pending_labs = 0
            
            context.update({
                'recent_records': recent_records,
                'recent_vitals': recent_vitals,
                'active_medications': active_medications,
                'pending_labs': pending_labs,
            })
            
        except Exception as e:
            logger.error(f"Error loading EMR dashboard: {str(e)}")
            context['error'] = 'Unable to load dashboard data.'
        
        return context


class MedicalRecordListView(ListView):
    """
    List all medical records
    """
    model = MedicalRecord
    template_name = 'emr/medical_record_list.html'
    context_object_name = 'medical_records'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = MedicalRecord.objects.filter(
            tenant=self.request.tenant
        ).select_related('patient').order_by('-record_date')
        
        # Apply search filter
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(patient__first_name__icontains=search) |
                Q(patient__last_name__icontains=search) |
                Q(chief_complaint__icontains=search) |
                Q(diagnosis__icontains=search)
            )
        
        return queryset


class MedicalRecordDetailView(DetailView):
    """
    Display medical record details
    """
    model = MedicalRecord
    template_name = 'emr/medical_record_detail.html'
    context_object_name = 'record'
    
    def get_queryset(self):
        return MedicalRecord.objects.filter(tenant=self.request.tenant)


class MedicalRecordCreateView(UnifiedSystemMixin, CreateView):
    """
    Create new medical record
    """
    model = MedicalRecord
    template_name = 'emr/medical_record_form.html'
    fields = [
        'patient', 'record_date', 'chief_complaint', 
        'history_of_present_illness', 'review_of_systems',
        'physical_examination', 'assessment_and_plan',
        'diagnosis', 'treatment_plan'
    ]
    
    def form_valid(self, form):
        form.instance.tenant = self.request.tenant
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Medical record created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('emr:medical_record_detail', kwargs={'pk': self.object.pk})


class MedicalRecordUpdateView(UpdateView):
    """
    Update medical record
    """
    model = MedicalRecord
    template_name = 'emr/medical_record_form.html'
    fields = [
        'chief_complaint', 'history_of_present_illness', 
        'review_of_systems', 'physical_examination',
        'assessment_and_plan', 'diagnosis', 'treatment_plan'
    ]
    
    def get_queryset(self):
        return MedicalRecord.objects.filter(tenant=self.request.tenant)
    
    def form_valid(self, form):
        messages.success(self.request, 'Medical record updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('emr:medical_record_detail', kwargs={'pk': self.object.pk})


class VitalSignsListView(ListView):
    """
    List vital signs
    """
    model = VitalSigns
    template_name = 'emr/vital_signs_list.html'
    context_object_name = 'vital_signs'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = VitalSigns.objects.filter(
            tenant=self.request.tenant
        ).select_related('patient').order_by('-recorded_at')
        
        # Apply patient filter
        patient_id = self.request.GET.get('patient')
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
        
        return queryset


class VitalSignsDetailView(DetailView):
    """
    Display vital signs details
    """
    model = VitalSigns
    template_name = 'emr/vital_signs_detail.html'
    context_object_name = 'vitals'
    
    def get_queryset(self):
        return VitalSigns.objects.filter(tenant=self.request.tenant)


class VitalSignsCreateView(UnifiedSystemMixin, CreateView):
    """
    Create new vital signs record
    """
    model = VitalSigns
    template_name = 'emr/vital_signs_form.html'
    fields = [
        'patient', 'recorded_at', 'blood_pressure_systolic',
        'blood_pressure_diastolic', 'heart_rate', 'temperature',
        'oxygen_saturation', 'respiratory_rate', 'weight', 'height'
    ]
    
    def form_valid(self, form):
        form.instance.tenant = self.request.tenant
        form.instance.recorded_by = self.request.user
        messages.success(self.request, 'Vital signs recorded successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('emr:vital_signs_detail', kwargs={'pk': self.object.pk})


class MedicationListView(ListView):
    """
    List medications
    """
    model = Medication
    template_name = 'emr/medication_list.html'
    context_object_name = 'medications'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Medication.objects.filter(
            tenant=self.request.tenant
        ).select_related('patient').order_by('-prescribed_date')
        
        # Apply filters
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        patient_id = self.request.GET.get('patient')
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
        
        return queryset


class MedicationDetailView(DetailView):
    """
    Display medication details
    """
    model = Medication
    template_name = 'emr/medication_detail.html'
    context_object_name = 'medication'
    
    def get_queryset(self):
        return Medication.objects.filter(tenant=self.request.tenant)


class MedicationCreateView(UnifiedSystemMixin, CreateView):
    """
    Create new medication record
    """
    model = Medication
    template_name = 'emr/medication_form.html'
    fields = [
        'patient', 'medication_name', 'dosage', 'frequency',
        'route', 'prescribed_date', 'start_date', 'end_date',
        'prescribing_doctor', 'instructions', 'status'
    ]
    
    def form_valid(self, form):
        form.instance.tenant = self.request.tenant
        messages.success(self.request, 'Medication added successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('emr:medication_detail', kwargs={'pk': self.object.pk})


class LabResultListView(ListView):
    """
    List lab results
    """
    model = LabResult
    template_name = 'emr/lab_result_list.html'
    context_object_name = 'lab_results'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = LabResult.objects.filter(
            tenant=self.request.tenant
        ).select_related('patient').order_by('-result_date')
        
        # Apply filters
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        patient_id = self.request.GET.get('patient')
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
        
        return queryset


class LabResultDetailView(DetailView):
    """
    Display lab result details
    """
    model = LabResult
    template_name = 'emr/lab_result_detail.html'
    context_object_name = 'lab_result'
    
    def get_queryset(self):
        return LabResult.objects.filter(tenant=self.request.tenant)


class LabResultCreateView(UnifiedSystemMixin, CreateView):
    """
    Create new lab result
    """
    model = LabResult
    template_name = 'emr/lab_result_form.html'
    fields = [
        'patient', 'test_name', 'test_category', 'result_value',
        'reference_range', 'units', 'result_date', 'status'
    ]
    
    def form_valid(self, form):
        form.instance.tenant = self.request.tenant
        form.instance.ordered_by = self.request.user
        messages.success(self.request, 'Lab result added successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('emr:lab_result_detail', kwargs={'pk': self.object.pk})


# Export API Views for use in URLs
AlertDetailAPIView = AlertDetailAPIView
RecommendationDetailAPIView = RecommendationDetailAPIView
PatientRiskAPIView = PatientRiskAPIView
ClinicalMetricsAPIView = ClinicalMetricsAPIView
AISystemStatusAPIView = AISystemStatusAPIView
