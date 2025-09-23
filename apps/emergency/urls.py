# emergency/urls.py (Emergency App URL Configuration)
from django.urls import path
from .views import (
    EmergencyDashboardView, EmergencyCaseCreateView, 
    EmergencyCaseUpdateView, EmergencyCaseDetailView, add_treatment
)

app_name = 'emergency'  # This is the namespace used in templates

urlpatterns = [
    path('', EmergencyDashboardView.as_view(), name='emergency_list'),  # Dashboard view
    path('case/create/', EmergencyCaseCreateView.as_view(), name='case_create'),  # Create case
    path('case/<int:pk>/update/', EmergencyCaseUpdateView.as_view(), name='case_update'),  # Update case
    path('case/<int:pk>/', EmergencyCaseDetailView.as_view(), name='case_detail'),  # Case detail
    path('case/<int:case_id>/add_treatment/', add_treatment, name='add_treatment'),  # Add treatment

    # Filter cases with HTMX (optional feature based on your dashboard)
    path('cases_filter/', EmergencyDashboardView.as_view(), name='cases_filter'),
]
