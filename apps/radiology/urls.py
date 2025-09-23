# apps/radiology/urls.py
from django.urls import path
from . import views

app_name = 'radiology'

urlpatterns = [
    # Dashboard
    path('', views.RadiologyDashboardView.as_view(), name='dashboard'),
    
    # Study Types Management
    path('study-types/', views.StudyTypeListView.as_view(), name='study_type_list'),
    path('study-types/create/', views.StudyTypeCreateView.as_view(), name='study_type_create'),
    path('study-types/<int:pk>/', views.StudyTypeDetailView.as_view(), name='study_type_detail'),
    path('study-types/<int:pk>/edit/', views.StudyTypeUpdateView.as_view(), name='study_type_update'),
    path('study-types/<int:pk>/delete/', views.StudyTypeDeleteView.as_view(), name='study_type_delete'),
    
    # Radiology Orders Management  
    path('orders/', views.RadiologyOrderListView.as_view(), name='order_list'),
    path('orders/create/', views.RadiologyOrderCreateView.as_view(), name='order_create'),
    path('orders/<uuid:pk>/', views.RadiologyOrderDetailView.as_view(), name='order_detail'),
    path('orders/<uuid:pk>/edit/', views.RadiologyOrderUpdateView.as_view(), name='order_update'),
    path('orders/<uuid:pk>/delete/', views.RadiologyOrderDeleteView.as_view(), name='order_delete'),
    
    # Imaging Studies Management
    path('studies/', views.ImagingStudyListView.as_view(), name='study_list'),
    path('studies/create/', views.ImagingStudyCreateView.as_view(), name='study_create'),
    path('studies/<uuid:pk>/', views.ImagingStudyDetailView.as_view(), name='study_detail'),
    path('studies/<uuid:pk>/edit/', views.ImagingStudyUpdateView.as_view(), name='study_update'),
    path('studies/<uuid:pk>/report/', views.RadiologistReportView.as_view(), name='study_report'),
    
    # Equipment Management
    path('equipment/', views.RadiologyEquipmentListView.as_view(), name='equipment_list'),
    path('equipment/create/', views.RadiologyEquipmentCreateView.as_view(), name='equipment_create'),
    path('equipment/<int:pk>/', views.RadiologyEquipmentDetailView.as_view(), name='equipment_detail'),
    path('equipment/<int:pk>/edit/', views.RadiologyEquipmentUpdateView.as_view(), name='equipment_update'),
    
    # API endpoints for AJAX calls
    path('api/patient-search/', views.PatientSearchAPIView.as_view(), name='patient_search_api'),
    path('api/study-types/', views.StudyTypeAPIView.as_view(), name='study_type_api'),
]
