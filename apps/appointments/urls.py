from django.urls import path
from . import views
from . import ai_views


app_name = 'appointments'

urlpatterns = [
    # Enhanced List and Detail Views
    path('', views.AppointmentListView.as_view(), name='appointment_list'),
    path('list/', views.appointment_list_enhanced, name='appointment_list_enhanced'),
    path('create/', views.AppointmentCreateView.as_view(), name='appointment_create'),
    path('create/enhanced/', views.appointment_create_enhanced, name='appointment_create_enhanced'),
    path('<uuid:pk>/', views.AppointmentDetailView.as_view(), name='appointment_detail'),
    path('<uuid:pk>/enhanced/', views.appointment_detail_enhanced, name='appointment_detail_enhanced'),
    path('edit/<uuid:pk>/', views.AppointmentUpdateView.as_view(), name='appointment_edit'),
    path('cancel/<uuid:pk>/', views.cancel_appointment, name='appointment_cancel'),

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
    
    # Patient History and Upcoming Appointments
    path('upcoming/', views.upcoming_appointments, name='upcoming'),
    path('upcoming/list/', views.upcoming_appointments_list, name='upcoming_appointments_list'),
    path('today/widget/', views.today_appointments_widget, name='today_appointments_widget'),
    path('patient/<uuid:patient_id>/history/', 
         views.patient_appointment_history, 
         name='patient_appointment_history'),

    # Appointment Actions
    path('<uuid:pk>/checkin/', views.check_in_appointment, name='check_in_appointment'),
    path('<uuid:pk>/start/', views.start_consultation, name='start_consultation'),
    path('<uuid:pk>/complete/', views.complete_appointment, name='complete_appointment'),
    path('<uuid:pk>/reschedule/', views.reschedule_appointment, name='reschedule_appointment'),
    path('<uuid:pk>/reminder/', views.send_reminder, name='send_reminder'),
    
    # Export and Reports
    path('export/', views.export_appointments, name='export'),
    path('<uuid:pk>/print/', views.print_appointment, name='print_appointment'),
    path('<uuid:pk>/export/pdf/', views.export_appointment_pdf, name='export_appointment_pdf'),
    
    # Modal Views
    path('<uuid:pk>/modal/', views.appointment_detail_modal, name='appointment_detail_modal'),
]