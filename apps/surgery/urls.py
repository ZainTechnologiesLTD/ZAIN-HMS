from django.urls import path
from .views import surgery_list_view

app_name = 'surgery'  # Register the namespace

urlpatterns = [
    path('', surgery_list_view, name='surgery_list'),  # Basic list view
]
