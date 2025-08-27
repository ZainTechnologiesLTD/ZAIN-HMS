# apps/tenants/urls.py
"""
URL Configuration for Tenant/Hospital Management
"""

from django.urls import path
from . import views

app_name = 'tenants'

urlpatterns = [
    # Multi-Tenant Hospital Management
    path('hospital-selection/', views.hospital_selection, name='hospital_selection'),
    path('switch-hospital/<int:hospital_id>/', views.switch_hospital, name='switch_hospital'),
    path('hospital-profile/', views.hospital_profile, name='hospital_profile'),
    path('subscription-details/', views.subscription_details, name='subscription_details'),
    path('hospital-settings/', views.hospital_settings, name='hospital_settings'),
]
