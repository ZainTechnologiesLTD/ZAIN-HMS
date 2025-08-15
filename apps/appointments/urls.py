from django.urls import path
from . import views


app_name = 'appointments'

urlpatterns = [
    # List and Detail Views
    path('', views.AppointmentListView.as_view(), name='appointment_list'),
    path('create/', views.AppointmentCreateView.as_view(), name='appointment_create'),
    path('<int:pk>/', views.AppointmentDetailView.as_view(), name='appointment_detail'),
    path('edit/<int:pk>/', views.AppointmentUpdateView.as_view(), name='appointment_edit'),
    path('cancel/<int:pk>/', views.cancel_appointment, name='appointment_cancel'),

    # Quick Schedule and Creation
    path('quick-schedule/', views.quick_schedule, name='quick_schedule'),
        
    # AJAX/HTMX Endpoints
    path('search-patients/', views.search_patients, name='search_patients'),
    path('get-doctors/', views.get_doctors, name='get_doctors'),
    path('get-doctor-schedule/', views.get_doctor_schedule, name='get_doctor_schedule'),
    path('check-availability/', views.check_availability, name='check_availability'),
    # Patient History and Upcoming Appointments
    path('upcoming/', views.upcoming_appointments, name='upcoming'),
    path('patient/<int:patient_id>/history/', 
         views.patient_appointment_history, 
         name='patient_appointment_history'),
]