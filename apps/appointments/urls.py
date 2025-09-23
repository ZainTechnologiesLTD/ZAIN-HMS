from django.urls import path
from django.shortcuts import redirect
from . import views
from . import ai_views
from . import notification_views


app_name = 'appointments'

urlpatterns = [
    # Enhanced List and Detail Views
    path('', views.AppointmentListView.as_view(), name='appointment_list'),
    path('list/', views.appointment_list_enhanced, name='appointment_list_enhanced'),
    # Redirect basic create to enhanced version
path('create/', views.appointment_create_super_enhanced, name='appointment_create'),
# Removed old appointment_create redirect to appointment_create_super_enhanced
path('create/enhanced/', views.appointment_create_super_enhanced, name='appointment_create_super_enhanced'),
    path('<uuid:pk>/', views.AppointmentDetailView.as_view(), name='appointment_detail'),
    path('<uuid:pk>/enhanced/', views.appointment_detail_enhanced, name='appointment_detail_enhanced'),
    path('edit/<uuid:pk>/', views.AppointmentUpdateView.as_view(), name='appointment_edit'),
    path('cancel/<uuid:pk>/', views.cancel_appointment, name='appointment_cancel'),
    
    # Enhanced API endpoints
    path('api/patient/<uuid:patient_id>/previous-appointments/', views.get_patient_previous_appointments, name='patient_previous_appointments'),

    # AI-Powered Scheduling
    path('ai/dashboard/', ai_views.AISchedulingDashboardView.as_view(), name='ai_dashboard'),
    path('ai/scheduling/', ai_views.AIOptimizedSchedulingView.as_view(), name='ai_scheduling'),
    path('ai/analytics/', ai_views.AIAppointmentAnalyticsView.as_view(), name='ai_analytics'),
    path('api/ai-scheduling/', ai_views.AISchedulingAPIView.as_view(), name='ai_scheduling_api'),

    # Calendar Views
    path('calendar/', views.appointment_calendar, name='appointment_calendar'),
    path('calendar/events/', views.calendar_events, name='calendar_events'),

    # Quick Schedule and Creation
    path('quick-schedule/', views.quick_schedule, name='quick_schedule'),
        
    # AJAX/HTMX Endpoints
    path('search-patients/', views.search_patients, name='search_patients'),
    path('get-doctors/', views.get_doctors, name='get_doctors'),
    path('get-doctor-schedule/', views.get_doctor_schedule, name='get_doctor_schedule'),
    path('get-available-time-slots/', views.get_available_time_slots, name='get_available_time_slots'),
    path('check-availability/', views.check_availability, name='check_availability'),
    
    # Enhanced appointment AJAX endpoints
    path('api/enhanced/create/', views.create_enhanced_appointment, name='create_enhanced_appointment'),
    path('api/enhanced/departments/', views.get_departments, name='get_departments'),
    path('api/enhanced/doctors/<int:department_id>/', views.get_doctors_by_department, name='get_doctors_by_department'),
    path('api/enhanced/time-slots/', views.get_enhanced_time_slots, name='get_enhanced_time_slots'),
    path('api/enhanced/month-availability/', views.get_month_availability_days, name='get_month_availability_days'),
    
    # Communication API endpoints
    path('api/appointments/communication-status/', views.communication_status_api, name='communication_status_api'),
    
    # Patient History and Upcoming Appointments
    path('upcoming/', views.upcoming_appointments, name='upcoming'),
    path('upcoming/list/', views.upcoming_appointments_list, name='upcoming_appointments_list'),
    path('today/widget/', views.today_appointments_widget, name='today_appointments_widget'),
    path('patient/<uuid:patient_id>/history/', 
         views.patient_appointment_history, 
         name='patient_appointment_history'),

    # Appointment Actions
    path('bulk-action/', views.bulk_appointment_action, name='bulk_appointment_action'),
    path('<uuid:pk>/checkin/', views.check_in_appointment, name='check_in_appointment'),
    path('<uuid:pk>/start/', views.start_consultation, name='start_consultation'),
    path('<uuid:pk>/complete/', views.complete_appointment, name='complete_appointment'),
    path('<uuid:pk>/reschedule/', views.reschedule_appointment, name='reschedule_appointment'),
    path('<uuid:pk>/reminder/', views.send_reminder, name='send_reminder'),
    
    # Export and Reports
    path('export/', views.export_appointments, name='export'),
    path('<uuid:pk>/print/', views.appointment_print, name='print_appointment'),
    path('<uuid:pk>/print-enhanced/', views.appointment_print, name='appointment_print'),
    path('<uuid:appointment_id>/generate-barcode/', views.generate_appointment_barcode, name='generate_appointment_barcode'),
    path('<uuid:pk>/export/pdf/', views.export_appointment_pdf, name='export_appointment_pdf'),
    
    # Modal Views (legacy route removed; use enhanced detail view instead)
    
    # Notification Management
    path('<uuid:appointment_id>/notifications/send/', notification_views.send_appointment_notification, name='send_notification'),
    path('<uuid:appointment_id>/notifications/send-bulk/', notification_views.send_bulk_notifications, name='send_bulk_notifications'),
    path('<uuid:appointment_id>/notifications/status/', notification_views.get_notification_status, name='notification_status'),
]