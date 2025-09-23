# apps/emr/admin.py
"""
EMR Admin Configuration with AI-Enhanced Clinical Decision Support
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    MedicalRecord, VitalSigns, Medication, LabResult,
    ClinicalAlert, ClinicalDecisionSupport
)


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    """
    Admin interface for Medical Records
    """
    list_display = [
        'patient', 'record_date', 'chief_complaint_short', 
        'diagnosis_short', 'ai_suggestions_indicator', 'created_at'
    ]
    list_filter = ['record_date', 'created_at']
    search_fields = [
        'patient__first_name', 'patient__last_name', 
        'chief_complaint', 'diagnosis'
    ]
    readonly_fields = ['created_at', 'updated_at', 'ai_diagnostic_suggestions']
    date_hierarchy = 'record_date'
    
    fieldsets = (
        ('Patient Information', {
            'fields': ('patient', 'record_date')
        }),
        ('Clinical Information', {
            'fields': (
                'chief_complaint', 'history_of_present_illness',
                'review_of_systems', 'physical_examination'
            )
        }),
        ('Assessment & Plan', {
            'fields': ('assessment_and_plan', 'diagnosis', 'treatment_plan')
        }),
        ('AI Insights', {
            'fields': ('ai_diagnostic_suggestions', 'ai_confidence_score'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def chief_complaint_short(self, obj):
        return obj.chief_complaint[:50] + '...' if len(obj.chief_complaint) > 50 else obj.chief_complaint
    chief_complaint_short.short_description = 'Chief Complaint'
    
    def diagnosis_short(self, obj):
        return obj.diagnosis[:50] + '...' if len(obj.diagnosis) > 50 else obj.diagnosis
    diagnosis_short.short_description = 'Diagnosis'
    
    def ai_suggestions_indicator(self, obj):
        if obj.ai_diagnostic_suggestions:
            return format_html(
                '<span style="color: green;"><i class="fas fa-brain"></i> AI</span>'
            )
        return '-'
    ai_suggestions_indicator.short_description = 'AI Insights'


@admin.register(VitalSigns)
class VitalSignsAdmin(admin.ModelAdmin):
    """
    Admin interface for Vital Signs
    """
    list_display = [
        'patient', 'recorded_at', 'blood_pressure', 'heart_rate',
        'temperature', 'ai_analysis_indicator', 'recorded_by'
    ]
    list_filter = ['recorded_at']
    search_fields = ['patient__first_name', 'patient__last_name']
    readonly_fields = ['ai_analysis_results']
    date_hierarchy = 'recorded_at'
    
    fieldsets = (
        ('Patient Information', {
            'fields': ('patient', 'recorded_at', 'recorded_by')
        }),
        ('Vital Signs', {
            'fields': (
                ('blood_pressure_systolic', 'blood_pressure_diastolic'),
                'heart_rate', 'temperature', 'oxygen_saturation',
                'respiratory_rate', ('weight', 'height')
            )
        }),
        ('AI Analysis', {
            'fields': ('ai_analysis_results', 'ai_alerts'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def blood_pressure(self, obj):
        if obj.blood_pressure_systolic and obj.blood_pressure_diastolic:
            return f"{obj.blood_pressure_systolic}/{obj.blood_pressure_diastolic}"
        return '-'
    blood_pressure.short_description = 'Blood Pressure'
    
    def ai_analysis_indicator(self, obj):
        if obj.ai_analysis_results:
            return format_html(
                '<span style="color: blue;"><i class="fas fa-chart-line"></i> Analyzed</span>'
            )
        return '-'
    ai_analysis_indicator.short_description = 'AI Analysis'


@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    """
    Admin interface for Medications
    """
    list_display = [
        'patient', 'medication_name', 'dosage', 'frequency',
        'status', 'interaction_check_indicator', 'start_date'
    ]
    list_filter = ['status', 'start_date', 'route']
    search_fields = [
        'patient__first_name', 'patient__last_name', 
        'medication_name'
    ]
    readonly_fields = ['created_at', 'updated_at', 'ai_interaction_analysis']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Patient Information', {
            'fields': ('patient', 'prescribing_doctor')
        }),
        ('Medication Details', {
            'fields': (
                'medication_name', 'dosage', 'frequency', 'route',
                'start_date', 'end_date',
                'instructions', 'status'
            )
        }),
        ('AI Drug Interaction Check', {
            'fields': ('ai_interaction_analysis', 'ai_risk_score'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def interaction_check_indicator(self, obj):
        if obj.ai_interaction_analysis:
            risk_score = obj.ai_risk_score or 0
            if risk_score >= 70:
                color = 'red'
                level = 'HIGH'
            elif risk_score >= 40:
                color = 'orange'
                level = 'MEDIUM'
            else:
                color = 'green'
                level = 'LOW'
            return format_html(
                f'<span style="color: {color};"><i class="fas fa-exclamation-triangle"></i> {level}</span>'
            )
        return '-'
    interaction_check_indicator.short_description = 'Interaction Risk'


@admin.register(LabResult)
class LabResultAdmin(admin.ModelAdmin):
    """
    Admin interface for Lab Results
    """
    list_display = [
        'patient', 'test_name', 'result_value', 'status',
        'ai_interpretation_indicator', 'result_date'
    ]
    list_filter = ['status', 'test_category', 'result_date']
    search_fields = [
        'patient__first_name', 'patient__last_name',
        'test_name'
    ]
    readonly_fields = ['created_at', 'ai_interpretation']
    date_hierarchy = 'result_date'
    
    fieldsets = (
        ('Patient Information', {
            'fields': ('patient', 'ordered_by')
        }),
        ('Test Information', {
            'fields': (
                'test_name', 'test_category', 'result_value',
                'reference_range', 'units', 'result_date', 'status'
            )
        }),
        ('AI Interpretation', {
            'fields': ('ai_interpretation', 'ai_clinical_significance'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def ai_interpretation_indicator(self, obj):
        if obj.ai_interpretation:
            return format_html(
                '<span style="color: purple;"><i class="fas fa-microscope"></i> Interpreted</span>'
            )
        return '-'
    ai_interpretation_indicator.short_description = 'AI Interpretation'


@admin.register(ClinicalAlert)
class ClinicalAlertAdmin(admin.ModelAdmin):
    """
    Admin interface for Clinical Alerts
    """
    list_display = [
        'title', 'patient', 'severity', 'alert_type', 
        'status', 'created_at', 'acknowledged_by'
    ]
    list_filter = ['severity', 'alert_type', 'status', 'created_at']
    search_fields = [
        'patient__first_name', 'patient__last_name',
        'title', 'description'
    ]
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Alert Information', {
            'fields': ('title', 'description', 'patient')
        }),
        ('Classification', {
            'fields': ('severity', 'alert_type', 'status')
        }),
        ('Resolution', {
            'fields': (
                'acknowledged_by', 'acknowledged_at',
                'resolution_notes'
            )
        }),
        ('Metadata', {
            'fields': ('metadata', 'created_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'patient', 'acknowledged_by'
        )


@admin.register(ClinicalDecisionSupport)
class ClinicalDecisionSupportAdmin(admin.ModelAdmin):
    """
    Admin interface for Clinical Decision Support
    """
    list_display = [
        'patient', 'recommendation_type', 'confidence_score',
        'is_implemented', 'created_at', 'implemented_by'
    ]
    list_filter = [
        'recommendation_type', 'is_implemented', 
        'created_at'
    ]
    search_fields = [
        'patient__first_name', 'patient__last_name',
        'recommendation_text'
    ]
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Patient Information', {
            'fields': ('patient', 'medical_record', 'doctor')
        }),
        ('Recommendation', {
            'fields': (
                'recommendation_type', 'recommendation_text',
                'confidence_score', 'supporting_evidence',
                'expected_outcome'
            )
        }),
        ('Implementation', {
            'fields': (
                'is_implemented', 'implemented_by',
                'implemented_at', 'implementation_notes'
            )
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'patient', 'doctor', 'implemented_by'
        )


# Customize admin site - handled by core app
