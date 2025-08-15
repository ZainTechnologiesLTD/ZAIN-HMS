from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.analytics_dashboard, name='dashboard'),
    path('patients/', views.patient_analytics, name='patient_analytics'),
    path('financial/', views.financial_analytics, name='financial_analytics'),
    path('api/chart-data/', views.api_chart_data, name='chart_data'),
]