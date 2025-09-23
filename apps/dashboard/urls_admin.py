# Enhanced Dashboard URLs
from django.urls import path
from . import views, views_admin

app_name = 'dashboard'

urlpatterns = [
    # Original dashboard
    path('', views.home, name='home'),
    
    # Enhanced dashboard
    path('enhanced/', views_admin.EnhancedDashboardView.as_view(), name='enhanced_home'),

    # API Endpoints for dashboard data
    path('api/stats/', views_admin.DashboardStatsAPIView.as_view(), name='api_stats'),
    path('api/notifications/', views_admin.NotificationsAPIView.as_view(), name='api_notifications'),
    path('api/activity/', views_admin.RecentActivityAPIView.as_view(), name='api_activity'),
    
    # Role-based dashboards
    path('admin/', views_admin.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('doctor/', views_admin.DoctorDashboardView.as_view(), name='doctor_dashboard'),
    path('nurse/', views_admin.NurseDashboardView.as_view(), name='nurse_dashboard'),
    path('receptionist/', views_admin.ReceptionistDashboardView.as_view(), name='receptionist_dashboard'),
    
    # Chart APIs
    path('api/charts/appointments/', views_admin.AppointmentChartAPIView.as_view(), name='api_chart_appointments'),
    path('api/charts/revenue/', views_enhanced.RevenueChartAPIView.as_view(), name='api_chart_revenue'),
    path('api/charts/patients/', views_enhanced.PatientChartAPIView.as_view(), name='api_chart_patients'),
]
