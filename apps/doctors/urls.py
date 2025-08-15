# doctors/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from django.contrib.auth import views as auth_views

router = DefaultRouter()


app_name = 'doctors'

urlpatterns = [
    # Normal Views
    path('list/', views.DoctorListView.as_view(), name='doctor_list'),
    path('<int:pk>/', views.DoctorDetailView.as_view(), name='doctor_detail'),
    path('create/', views.DoctorCreateView.as_view(), name='doctor_create'),
    path('<int:pk>/update/', views.DoctorUpdateView.as_view(), name='doctor_update'),

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
