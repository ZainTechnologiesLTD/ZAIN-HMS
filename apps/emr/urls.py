# apps/emr/urls.py
"""
EMR URL Configuration with AI-Enhanced Clinical Decision Support
"""

from django.urls import path
from . import views, ai_views

app_name = 'emr'

urlpatterns = [
    # Traditional EMR URLs
    path('', views.EMRDashboardView.as_view(), name='dashboard'),
    path('medical-records/', views.MedicalRecordListView.as_view(), name='medical_record_list'),
    path('medical-records/create/', views.MedicalRecordCreateView.as_view(), name='medical_record_create'),
    path('medical-records/<int:pk>/', views.MedicalRecordDetailView.as_view(), name='medical_record_detail'),
    path('medical-records/<int:pk>/edit/', views.MedicalRecordUpdateView.as_view(), name='medical_record_edit'),
    
    # Vital Signs URLs
    path('vital-signs/', views.VitalSignsListView.as_view(), name='vital_signs_list'),
    path('vital-signs/create/', views.VitalSignsCreateView.as_view(), name='vital_signs_create'),
    path('vital-signs/<int:pk>/', views.VitalSignsDetailView.as_view(), name='vital_signs_detail'),
    
    # Medications URLs
    path('medications/', views.MedicationListView.as_view(), name='medication_list'),
    path('medications/create/', views.MedicationCreateView.as_view(), name='medication_create'),
    path('medications/<int:pk>/', views.MedicationDetailView.as_view(), name='medication_detail'),
    
    # Lab Results URLs
    path('lab-results/', views.LabResultListView.as_view(), name='lab_result_list'),
    path('lab-results/create/', views.LabResultCreateView.as_view(), name='lab_result_create'),
    path('lab-results/<int:pk>/', views.LabResultDetailView.as_view(), name='lab_result_detail'),
    
    # AI-Enhanced Clinical Decision Support URLs
    path('ai/', ai_views.AIClinicalDashboardView.as_view(), name='ai_dashboard'),
    path('ai/patient-analysis/<int:patient_id>/', ai_views.AIPatientAnalysisView.as_view(), name='ai_patient_analysis'),
    path('ai/clinical-decisions/', ai_views.AIClinicalDecisionView.as_view(), name='ai_clinical_decisions'),
    path('ai/clinical-alerts/', ai_views.AIClinicalAlertsView.as_view(), name='ai_clinical_alerts'),
    
    # AI Action URLs
    path('alerts/<int:alert_id>/action/', ai_views.AIAlertActionView.as_view(), name='ai_alert_action'),
    
    # AI Analysis API URLs
    path('ai/vital-signs-analysis/', ai_views.AIVitalSignsAnalysisView.as_view(), name='ai_vital_signs_analysis'),
    path('ai/drug-interactions/', ai_views.AIDrugInteractionView.as_view(), name='ai_drug_interactions'),
    path('ai/lab-analysis/', ai_views.AILabResultsAnalysisView.as_view(), name='ai_lab_analysis'),
    path('ai/treatment-plan/', ai_views.AITreatmentPlanView.as_view(), name='ai_treatment_plan'),
    
    # API Endpoints for AJAX requests
    path('api/alert/<int:alert_id>/', views.AlertDetailAPIView.as_view(), name='api_alert_detail'),
    path('api/recommendation/<int:rec_id>/', views.RecommendationDetailAPIView.as_view(), name='api_recommendation_detail'),
    path('api/patient-risk/<int:patient_id>/', views.PatientRiskAPIView.as_view(), name='api_patient_risk'),
    path('api/clinical-metrics/', views.ClinicalMetricsAPIView.as_view(), name='api_clinical_metrics'),
    path('api/ai-system-status/', views.AISystemStatusAPIView.as_view(), name='api_ai_system_status'),
]
