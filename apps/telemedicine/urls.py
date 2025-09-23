# apps/telemedicine/urls.py
from django.urls import path
from . import views

app_name = 'telemedicine'

urlpatterns = [
    path('', views.telemedicine_dashboard, name='dashboard'),
    path('teleconsultations/', views.teleconsultation_list, name='teleconsultation_list'),
    path('consultation/<int:appointment_id>/', views.virtual_consultation_room, name='virtual_room'),
    path('join/<int:appointment_id>/', views.join_consultation, name='join_consultation'),
]
