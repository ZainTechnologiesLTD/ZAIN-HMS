# apps/emr/models.py
"""
Enhanced Electronic Medical Records (EMR) Models with AI Clinical Decision Support
"""

import uuid
import json
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.accounts.models import CustomUser as User
from apps.patients.models import Patient
from apps.doctors.models import Doctor
from apps.appointments.models import Appointment


class MedicalRecord(models.Model):
    """
    Comprehensive medical record for a patient
    """
    
    RECORD_TYPE_CHOICES = [
        ('CONSULTATION', 'Consultation'),
        ('ADMISSION', 'Hospital Admission'),
        ('EMERGENCY', 'Emergency Visit'),
        ('FOLLOW_UP', 'Follow-up Visit'),
        ('PROCEDURE', 'Medical Procedure'),
        ('DISCHARGE', 'Discharge Summary'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic Information
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_records')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='medical_records')
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True)
    
    record_type = models.CharField(max_length=20, choices=RECORD_TYPE_CHOICES, default='CONSULTATION')
    record_date = models.DateTimeField(default=timezone.now)
    
    # Clinical Information
    chief_complaint = models.TextField(help_text="Primary reason for visit")
    history_of_present_illness = models.TextField(blank=True, help_text="Detailed history of current illness")
    review_of_systems = models.TextField(blank=True, help_text="Review of systems")
    
    # Physical Examination
    physical_examination = models.TextField(blank=True, help_text="Physical examination findings")
    
    # Assessment and Plan
    clinical_assessment = models.TextField(blank=True, help_text="Clinical assessment and diagnosis")
    treatment_plan = models.TextField(blank=True, help_text="Treatment plan and recommendations")
    
    # AI-Enhanced Fields
    ai_diagnostic_suggestions = models.TextField(blank=True, help_text="AI-generated diagnostic suggestions (JSON)")
    ai_treatment_recommendations = models.TextField(blank=True, help_text="AI treatment recommendations (JSON)")
    ai_risk_assessment = models.TextField(blank=True, help_text="AI risk assessment (JSON)")
    ai_confidence_score = models.FloatField(null=True, blank=True, help_text="AI confidence score (0.0-1.0)")
    
    # Follow-up
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)
    follow_up_instructions = models.TextField(blank=True)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_medical_records')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-record_date']
        indexes = [
            models.Index(fields=['patient', 'record_date']),
            models.Index(fields=['doctor', 'record_date']),
            models.Index(fields=['record_type']),
        ]
    
    def __str__(self):
        return f"{self.patient.get_full_name()} - {self.record_type} on {self.record_date.date()}"
    
    def get_ai_diagnostic_suggestions(self):
        """Parse AI diagnostic suggestions from JSON"""
        try:
            return json.loads(self.ai_diagnostic_suggestions) if self.ai_diagnostic_suggestions else []
        except json.JSONDecodeError:
            return []
    
    def set_ai_diagnostic_suggestions(self, suggestions):
        """Set AI diagnostic suggestions as JSON"""
        self.ai_diagnostic_suggestions = json.dumps(suggestions)
    
    def get_ai_treatment_recommendations(self):
        """Parse AI treatment recommendations from JSON"""
        try:
            return json.loads(self.ai_treatment_recommendations) if self.ai_treatment_recommendations else []
        except json.JSONDecodeError:
            return []
    
    def set_ai_treatment_recommendations(self, recommendations):
        """Set AI treatment recommendations as JSON"""
        self.ai_treatment_recommendations = json.dumps(recommendations)


class VitalSigns(models.Model):
    """
    Patient vital signs with AI analysis
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Patient Information
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='vital_signs')
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='vital_signs', null=True, blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='recorded_vital_signs')
    recorded_at = models.DateTimeField(default=timezone.now)
    
    # Vital Signs Measurements
    blood_pressure_systolic = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(50), MaxValueValidator(250)],
        help_text="Systolic blood pressure (mmHg)"
    )
    blood_pressure_diastolic = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(30), MaxValueValidator(150)],
        help_text="Diastolic blood pressure (mmHg)"
    )
    heart_rate = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(30), MaxValueValidator(200)],
        help_text="Heart rate (beats per minute)"
    )
    respiratory_rate = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(8), MaxValueValidator(50)],
        help_text="Respiratory rate (breaths per minute)"
    )
    temperature = models.DecimalField(
        max_digits=4, decimal_places=1,
        null=True, blank=True,
        validators=[MinValueValidator(30.0), MaxValueValidator(45.0)],
        help_text="Body temperature (°C)"
    )
    oxygen_saturation = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(70), MaxValueValidator(100)],
        help_text="Oxygen saturation (%)"
    )
    weight = models.DecimalField(
        max_digits=5, decimal_places=1,
        null=True, blank=True,
        validators=[MinValueValidator(0.5), MaxValueValidator(300.0)],
        help_text="Weight (kg)"
    )
    height = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(30), MaxValueValidator(250)],
        help_text="Height (cm)"
    )
    
    # AI Analysis Results
    ai_analysis_results = models.TextField(blank=True, help_text="AI analysis of vital signs (JSON)")
    ai_alerts = models.TextField(blank=True, help_text="AI-generated alerts (JSON)")
    ai_recommendations = models.TextField(blank=True, help_text="AI recommendations (JSON)")
    overall_health_score = models.FloatField(null=True, blank=True, help_text="AI-calculated health score")
    
    # Notes
    notes = models.TextField(blank=True, help_text="Additional notes about vital signs")
    
    class Meta:
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['patient', 'recorded_at']),
            models.Index(fields=['recorded_at']),
        ]
    
    def __str__(self):
        return f"Vital Signs for {self.patient.get_full_name()} on {self.recorded_at.date()}"
    
    @property
    def bmi(self):
        """Calculate BMI if height and weight are available"""
        if self.height and self.weight:
            height_m = float(self.height) / 100
            return round(float(self.weight) / (height_m ** 2), 1)
        return None
    
    @property
    def blood_pressure(self):
        """Return formatted blood pressure"""
        if self.blood_pressure_systolic and self.blood_pressure_diastolic:
            return f"{self.blood_pressure_systolic}/{self.blood_pressure_diastolic}"
        return None
    
    def get_ai_analysis_results(self):
        """Parse AI analysis results from JSON"""
        try:
            return json.loads(self.ai_analysis_results) if self.ai_analysis_results else {}
        except json.JSONDecodeError:
            return {}
    
    def set_ai_analysis_results(self, results):
        """Set AI analysis results as JSON"""
        self.ai_analysis_results = json.dumps(results)
    
    def get_ai_alerts(self):
        """Parse AI alerts from JSON"""
        try:
            return json.loads(self.ai_alerts) if self.ai_alerts else []
        except json.JSONDecodeError:
            return []
    
    def set_ai_alerts(self, alerts):
        """Set AI alerts as JSON"""
        self.ai_alerts = json.dumps(alerts)


class Medication(models.Model):
    """
    Patient medications with AI interaction checking
    """
    
    FREQUENCY_CHOICES = [
        ('ONCE_DAILY', 'Once Daily'),
        ('TWICE_DAILY', 'Twice Daily'),
        ('THREE_TIMES_DAILY', 'Three Times Daily'),
        ('FOUR_TIMES_DAILY', 'Four Times Daily'),
        ('AS_NEEDED', 'As Needed'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('DISCONTINUED', 'Discontinued'),
        ('SUSPENDED', 'Suspended'),
        ('COMPLETED', 'Completed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Patient and Record Information
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medications')
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='medications', null=True, blank=True)
    prescribed_by = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='prescribed_medications')
    
    # Medication Details
    medication_name = models.CharField(max_length=200, help_text="Generic or brand name")
    dosage = models.CharField(max_length=100, help_text="Dosage (e.g., 10mg, 5ml)")
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='ONCE_DAILY')
    route = models.CharField(max_length=50, default='Oral', help_text="Route of administration")
    
    # Duration and Status
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    
    # Instructions
    instructions = models.TextField(blank=True, help_text="Special instructions for taking medication")
    indication = models.CharField(max_length=200, blank=True, help_text="Reason for prescription")
    
    # AI Drug Interaction Analysis
    ai_interaction_analysis = models.TextField(blank=True, help_text="AI drug interaction analysis (JSON)")
    ai_contraindication_alerts = models.TextField(blank=True, help_text="AI contraindication alerts (JSON)")
    ai_risk_score = models.FloatField(null=True, blank=True, help_text="AI-calculated risk score")
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_medications')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['prescribed_by']),
            models.Index(fields=['start_date']),
        ]
    
    def __str__(self):
        return f"{self.medication_name} - {self.dosage} {self.frequency} for {self.patient.get_full_name()}"
    
    def get_ai_interaction_analysis(self):
        """Parse AI interaction analysis from JSON"""
        try:
            return json.loads(self.ai_interaction_analysis) if self.ai_interaction_analysis else {}
        except json.JSONDecodeError:
            return {}
    
    def set_ai_interaction_analysis(self, analysis):
        """Set AI interaction analysis as JSON"""
        self.ai_interaction_analysis = json.dumps(analysis)


class LabResult(models.Model):
    """
    Laboratory test results with AI interpretation
    """
    
    STATUS_CHOICES = [
        ('NORMAL', 'Normal'),
        ('ABNORMAL', 'Abnormal'),
        ('CRITICAL', 'Critical'),
        ('PENDING', 'Pending'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Patient and Record Information
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='lab_results')
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='lab_results', null=True, blank=True)
    ordered_by = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='ordered_lab_results')
    
    # Test Information
    test_name = models.CharField(max_length=200, help_text="Name of the laboratory test")
    test_code = models.CharField(max_length=50, blank=True, help_text="Laboratory test code")
    test_category = models.CharField(max_length=100, blank=True, help_text="Test category (e.g., Chemistry, Hematology)")
    
    # Results
    result_value = models.CharField(max_length=200, help_text="Test result value")
    result_unit = models.CharField(max_length=50, blank=True, help_text="Unit of measurement")
    reference_range = models.CharField(max_length=200, blank=True, help_text="Normal reference range")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Dates
    ordered_date = models.DateTimeField(default=timezone.now)
    sample_collected_date = models.DateTimeField(null=True, blank=True)
    result_date = models.DateTimeField(null=True, blank=True)
    
    # AI Analysis
    ai_interpretation = models.TextField(blank=True, help_text="AI interpretation of lab result (JSON)")
    ai_clinical_significance = models.TextField(blank=True, help_text="AI assessment of clinical significance")
    ai_recommendations = models.TextField(blank=True, help_text="AI-generated recommendations (JSON)")
    ai_confidence_score = models.FloatField(null=True, blank=True, help_text="AI confidence in interpretation")
    
    # Notes
    technician_notes = models.TextField(blank=True, help_text="Laboratory technician notes")
    physician_notes = models.TextField(blank=True, help_text="Physician interpretation notes")
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_lab_results')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-result_date', '-ordered_date']
        indexes = [
            models.Index(fields=['patient', 'result_date']),
            models.Index(fields=['test_name', 'status']),
            models.Index(fields=['ordered_date']),
        ]
    
    def __str__(self):
        return f"{self.test_name} for {self.patient.get_full_name()} - {self.result_value}"
    
    def get_ai_interpretation(self):
        """Parse AI interpretation from JSON"""
        try:
            return json.loads(self.ai_interpretation) if self.ai_interpretation else {}
        except json.JSONDecodeError:
            return {}
    
    def set_ai_interpretation(self, interpretation):
        """Set AI interpretation as JSON"""
        self.ai_interpretation = json.dumps(interpretation)
    
    def get_ai_recommendations(self):
        """Parse AI recommendations from JSON"""
        try:
            return json.loads(self.ai_recommendations) if self.ai_recommendations else []
        except json.JSONDecodeError:
            return []
    
    def set_ai_recommendations(self, recommendations):
        """Set AI recommendations as JSON"""
        self.ai_recommendations = json.dumps(recommendations)


class ClinicalAlert(models.Model):
    """
    AI-generated clinical alerts for patient care
    """
    
    ALERT_TYPE_CHOICES = [
        ('CRITICAL_VITAL', 'Critical Vital Signs'),
        ('ABNORMAL_LAB', 'Abnormal Lab Results'),
        ('DRUG_INTERACTION', 'Drug Interaction'),
        ('ALLERGIC_REACTION', 'Allergic Reaction Risk'),
        ('CONTRAINDICATION', 'Medical Contraindication'),
        ('FOLLOW_UP_REQUIRED', 'Follow-up Required'),
        ('DIAGNOSTIC_SUGGESTION', 'Diagnostic Suggestion'),
    ]
    
    SEVERITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('ACKNOWLEDGED', 'Acknowledged'),
        ('RESOLVED', 'Resolved'),
        ('DISMISSED', 'Dismissed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Patient and Context
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='clinical_alerts')
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.SET_NULL, null=True, blank=True, related_name='clinical_alerts')
    
    # Alert Details
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPE_CHOICES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    title = models.CharField(max_length=200, help_text="Brief alert title")
    message = models.TextField(help_text="Detailed alert message")
    
    # AI Analysis
    ai_confidence = models.FloatField(help_text="AI confidence in alert (0.0-1.0)")
    ai_reasoning = models.TextField(blank=True, help_text="AI reasoning for generating alert")
    ai_recommendations = models.TextField(blank=True, help_text="AI-recommended actions (JSON)")
    
    # Status and Resolution
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='acknowledged_alerts')
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True, help_text="Notes on how alert was resolved")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['severity', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.alert_type} - {self.severity} for {self.patient.get_full_name()}"
    
    def acknowledge(self, user):
        """Acknowledge the alert"""
        self.status = 'ACKNOWLEDGED'
        self.acknowledged_by = user
        self.acknowledged_at = timezone.now()
        self.save()
    
    def resolve(self, user, notes=""):
        """Resolve the alert"""
        self.status = 'RESOLVED'
        self.acknowledged_by = user
        self.acknowledged_at = timezone.now()
        self.resolution_notes = notes
        self.save()
    
    def get_ai_recommendations(self):
        """Parse AI recommendations from JSON"""
        try:
            return json.loads(self.ai_recommendations) if self.ai_recommendations else []
        except json.JSONDecodeError:
            return []
    
    def set_ai_recommendations(self, recommendations):
        """Set AI recommendations as JSON"""
        self.ai_recommendations = json.dumps(recommendations)


class ClinicalDecisionSupport(models.Model):
    """
    AI clinical decision support recommendations
    """
    
    RECOMMENDATION_TYPE_CHOICES = [
        ('DIAGNOSTIC', 'Diagnostic Recommendation'),
        ('TREATMENT', 'Treatment Recommendation'),
        ('MEDICATION', 'Medication Recommendation'),
        ('MONITORING', 'Monitoring Recommendation'),
        ('FOLLOW_UP', 'Follow-up Recommendation'),
        ('LIFESTYLE', 'Lifestyle Recommendation'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Patient and Context
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='clinical_decisions')
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='clinical_decisions')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='received_clinical_decisions')
    
    # Recommendation Details
    recommendation_type = models.CharField(max_length=20, choices=RECOMMENDATION_TYPE_CHOICES)
    title = models.CharField(max_length=200, help_text="Brief recommendation title")
    description = models.TextField(help_text="Detailed recommendation description")
    
    # AI Analysis
    ai_reasoning = models.TextField(help_text="AI reasoning behind recommendation")
    confidence_score = models.FloatField(help_text="AI confidence in recommendation (0.0-1.0)")
    supporting_evidence = models.TextField(blank=True, help_text="Supporting medical evidence (JSON)")
    
    # Implementation
    is_implemented = models.BooleanField(default=False)
    implementation_notes = models.TextField(blank=True, help_text="Notes on implementation")
    implemented_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='implemented_decisions')
    implemented_at = models.DateTimeField(null=True, blank=True)
    
    # Outcome Tracking
    outcome_tracked = models.BooleanField(default=False)
    outcome_notes = models.TextField(blank=True, help_text="Notes on outcome")
    effectiveness_score = models.FloatField(null=True, blank=True, help_text="Effectiveness rating (0.0-1.0)")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['patient', 'is_implemented']),
            models.Index(fields=['doctor', 'created_at']),
            models.Index(fields=['recommendation_type']),
        ]
    
    def __str__(self):
        return f"{self.recommendation_type} for {self.patient.get_full_name()}"
    
    def implement(self, user, notes=""):
        """Mark recommendation as implemented"""
        self.is_implemented = True
        self.implemented_by = user
        self.implemented_at = timezone.now()
        self.implementation_notes = notes
        self.save()
    
    def get_supporting_evidence(self):
        """Parse supporting evidence from JSON"""
        try:
            return json.loads(self.supporting_evidence) if self.supporting_evidence else []
        except json.JSONDecodeError:
            return []
    
    def set_supporting_evidence(self, evidence):
        """Set supporting evidence as JSON"""
        self.supporting_evidence = json.dumps(evidence)
