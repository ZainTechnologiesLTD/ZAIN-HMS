# apps/reports/urls.py
from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Report Management
    path('', views.ReportListView.as_view(), name='report_list'),
    path('generate/', views.GenerateReportView.as_view(), name='generate_report'),
    path('<uuid:pk>/', views.ReportDetailView.as_view(), name='report_detail'),
    path('<uuid:pk>/download/', views.download_report, name='download_report'),
    path('<uuid:pk>/delete/', views.delete_report, name='delete_report'),
    
    # Report Templates
    path('templates/', views.ReportTemplateListView.as_view(), name='template_list'),
    path('templates/create/', views.ReportTemplateCreateView.as_view(), name='template_create'),
    path('templates/<uuid:pk>/edit/', views.ReportTemplateUpdateView.as_view(), name='template_edit'),
    path('templates/<uuid:pk>/use/', views.use_template, name='use_template'),
    
    # Quick Reports
    path('quick/patients/', views.patients_report, name='quick_patients'),
    path('quick/appointments/', views.appointments_report, name='quick_appointments'),
    path('quick/billing/', views.billing_report, name='quick_billing'),
    path('quick/financial/', views.financial_report, name='quick_financial'),
    path('test/financial/', views.test_financial_report, name='test_financial'),  # Temporary test endpoint
    
    # Summary Reports
    path('doctor-performance/', views.doctor_performance_report, name='doctor_performance'),
    path('inventory-summary/', views.inventory_summary_report, name='inventory_summary'),
    path('lab-summary/', views.lab_summary_report, name='lab_summary'),
    path('patient-summary/', views.patient_summary_report, name='patient_summary'),
    
    # Financial Dashboard
    path('financial/', views.financial_dashboard, name='financial_dashboard'),
]
