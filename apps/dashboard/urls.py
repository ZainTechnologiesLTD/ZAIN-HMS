# dashboard/urls.py
from django.urls import path, include
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='dashboard'),
    path('home/', views.dashboard_home, name='home'),
    
    # Enhanced dashboard endpoints - check if this exists before enabling
    # path('enhanced/', include('apps.dashboard.urls_enhanced')),
]