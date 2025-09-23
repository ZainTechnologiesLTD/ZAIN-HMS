# apps/inventory/urls.py
from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Inventory management URLs - placeholder for future implementation
    path('', views.inventory_dashboard, name='dashboard'),
]
