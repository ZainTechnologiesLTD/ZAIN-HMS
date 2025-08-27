# Enhanced Dashboard URLs
from django.urls import path
from . import views, views_enhanced

app_name = 'dashboard'

urlpatterns = [
    # Original dashboard
    path('', views.home, name='home'),
    
    # Enhanced dashboard
    path('enhanced/', views_enhanced.EnhancedDashboardView.as_view(), name='enhanced_home'),
    
    # API endpoints for real-time data
    path('api/stats/', views_enhanced.DashboardStatsAPIView.as_view(), name='api_stats'),
    path('api/notifications/', views_enhanced.NotificationsAPIView.as_view(), name='api_notifications'),
    path('api/activity/', views_enhanced.RecentActivityAPIView.as_view(), name='api_activity'),
    
    # Role-specific dashboards
    path('admin/', views_enhanced.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('doctor/', views_enhanced.DoctorDashboardView.as_view(), name='doctor_dashboard'),
    path('nurse/', views_enhanced.NurseDashboardView.as_view(), name='nurse_dashboard'),
    path('receptionist/', views_enhanced.ReceptionistDashboardView.as_view(), name='receptionist_dashboard'),
    
    # Chart data endpoints
    path('api/charts/appointments/', views_enhanced.AppointmentChartAPIView.as_view(), name='api_chart_appointments'),
    path('api/charts/revenue/', views_enhanced.RevenueChartAPIView.as_view(), name='api_chart_revenue'),
    path('api/charts/patients/', views_enhanced.PatientChartAPIView.as_view(), name='api_chart_patients'),
]
