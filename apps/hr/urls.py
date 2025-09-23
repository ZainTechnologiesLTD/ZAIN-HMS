# apps/hr/urls.py
from django.urls import path
from . import views

app_name = 'hr'

urlpatterns = [
    # HR management URLs - placeholder for future implementation
    path('', views.hr_dashboard, name='dashboard'),
]
