# apps/pharmacy/pos_urls.py
from django.urls import path
from . import pos_views

app_name = 'pharmacy_pos'

urlpatterns = [
    # PoS Dashboard and Main Interface
    path('pos/', pos_views.pos_dashboard, name='dashboard'),
    path('pos/sale/', pos_views.pos_sale_interface, name='sale_interface'),
    
    # AJAX APIs for PoS
    path('pos/api/search-medicines/', pos_views.api_search_medicines, name='api_search_medicines'),
    path('pos/api/search-patients/', pos_views.api_search_patients, name='api_search_patients'),
    path('pos/api/prescription-details/', pos_views.api_get_prescription_details, name='api_prescription_details'),
    path('pos/api/checkout/', pos_views.api_process_checkout, name='api_checkout'),
    
    # Transaction Management
    path('pos/transactions/', pos_views.transaction_history, name='transaction_history'),
    path('pos/transaction/<uuid:transaction_id>/', pos_views.transaction_detail, name='transaction_detail'),
    path('pos/receipt/<uuid:transaction_id>/', pos_views.print_receipt, name='print_receipt'),
    
    # Day Close
    path('pos/day-close/', pos_views.day_close, name='day_close'),
]
