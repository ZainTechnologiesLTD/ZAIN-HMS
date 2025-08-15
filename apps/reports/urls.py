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
]
