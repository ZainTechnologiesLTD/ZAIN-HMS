# pharmacy/urls.py
from django.urls import path
from . import views

app_name = 'pharmacy'  # Namespace registration

urlpatterns = [
    # Dashboard
    path('', views.pharmacy_dashboard, name='dashboard'),
    
    # Medicines
    path('medicines/', views.medicine_list_view, name='medicine_list'),
    path('api/medicine-search/', views.medicine_search_api, name='medicine_search_api'),
    
    # Sales/Bills
    path('bills/', views.bill_list_view, name='bill_list'),
    path('bills/<int:bill_id>/', views.bill_detail_view, name='bill_detail'),
    path('sales/create/', views.create_sale_view, name='create_sale'),
    path('bills/<int:sale_id>/print/', views.print_bill_view, name='print_bill'),
    
    # Prescriptions
    path('prescriptions/', views.prescription_list_view, name='prescription_list'),
    path('prescriptions/<int:prescription_id>/fulfill/', views.fulfill_prescription_view, name='fulfill_prescription'),
    
    # Reports
    path('reports/stock/', views.stock_report_view, name='stock_report'),
]
