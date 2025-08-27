# doctors/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from django.contrib.auth import views as auth_views

router = DefaultRouter()


app_name = 'doctors'

urlpatterns = [
    # Normal Views
    path('', views.DoctorListView.as_view(), name='doctor_list'),  # Main list view
    path('list/', views.DoctorListView.as_view(), name='doctor_list_alt'),  # Alternative path
    path('<int:pk>/', views.DoctorDetailView.as_view(), name='doctor_detail'),
    path('create/', views.DoctorCreateView.as_view(), name='doctor_create'),
    path('<int:pk>/update/', views.DoctorUpdateView.as_view(), name='doctor_update'),
    path('<int:pk>/delete/', views.DoctorDeleteView.as_view(), name='doctor_delete'),
    
    # Doctor Dashboard and Personal Views
    path('dashboard/', views.DoctorDashboardView.as_view(), name='doctor_dashboard'),
    path('my-appointments/', views.DoctorAppointmentsView.as_view(), name='doctor_appointments'),
    path('my-prescriptions/', views.DoctorPrescriptionsView.as_view(), name='doctor_prescriptions'),
    
    # Prescription Management
    path('prescriptions/create/', views.CreatePrescriptionView.as_view(), name='create_prescription'),
    path('prescriptions/create/<uuid:appointment_id>/', views.CreatePrescriptionView.as_view(), name='create_prescription_from_appointment'),
    path('prescriptions/<uuid:pk>/', views.PrescriptionDetailView.as_view(), name='prescription_detail'),
    
    # User Management for Doctors
    path('<int:pk>/create-user/', views.CreateUserForDoctorView.as_view(), name='create_user_for_doctor'),
    path('<int:pk>/link-user/', views.LinkDoctorUserView.as_view(), name='link_user'),
    path('<int:pk>/unlink-user/', views.unlink_doctor_user, name='unlink_user'),
    path('without-users/', views.DoctorsWithoutUsersView.as_view(), name='doctors_without_users'),

     # Password Reset URLs - Required for the email link to work
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='doctors/password_reset_form.html',
             email_template_name='doctors/password_reset_email.html',
             success_url='/doctors/password_reset/done/'
         ),
         name='password_reset'),
    
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='doctors/password_reset_done.html'
         ),
         name='password_reset_done'),
    
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='doctors/password_reset_confirm.html',
             success_url='/doctors/password_reset_complete/'
         ),
         name='password_reset_confirm'),
    
    path('password_reset_complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='doctors/password_reset_complete.html'
         ),
         name='password_reset_complete'),

    # API Views
    # path('api/', include(router.urls)),
    # path('api/create-prescription/', create_prescription, name='create-prescription'),
]
