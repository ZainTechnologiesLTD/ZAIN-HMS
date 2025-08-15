from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PatientListView, PatientDetailView, PatientCreateView, PatientUpdateView, PatientQuickAddView, PatientDeleteView


app_name = 'patients'

urlpatterns = [
    path('', PatientListView.as_view(), name='patient_list'),
    path('<int:pk>/', PatientDetailView.as_view(), name='patient_detail'),
    path('create/', PatientCreateView.as_view(), name='patient_create'),
    path('<int:pk>/update/', PatientUpdateView.as_view(), name='patient_update'),
    path('quick_add/', PatientQuickAddView.as_view(), name='quick_add'),
    path('patients/<int:pk>/delete_modal/', PatientDeleteView.as_view(), name='patient_delete_modal'),
  
   ]
