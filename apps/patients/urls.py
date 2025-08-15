# apps/patients/urls.py
from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    path('', views.PatientListView.as_view(), name='list'),
    path('create/', views.PatientCreateView.as_view(), name='create'),
    path('<uuid:pk>/', views.PatientDetailView.as_view(), name='detail'),
    path('<uuid:pk>/edit/', views.PatientUpdateView.as_view(), name='update'),
    path('<uuid:pk>/delete/', views.PatientDeleteView.as_view(), name='delete'),
    path('quick-register/', views.quick_patient_register, name='quick_register'),
    path('search/', views.patient_search_api, name='search_api'),
    path('<uuid:patient_id>/documents/add/', views.add_patient_document, name='add_document'),
    path('<uuid:patient_id>/notes/add/', views.add_patient_note, name='add_note'),
    path('<uuid:patient_id>/vitals/add/', views.add_patient_vitals, name='add_vitals'),
]