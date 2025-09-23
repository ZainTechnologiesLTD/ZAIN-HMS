# apps/billing/pos_urls.py
from django.urls import path
from . import pos_views

# No app_name here since these URLs are included in billing.urls.py which has app_name = 'billing'

urlpatterns = [
    # PoS Dashboard
    path('pos/', pos_views.pos_dashboard, name='pos_dashboard'),
    
    # Sales Interface
    path('pos/sale/', pos_views.pos_sale_interface, name='pos_sale'),
    path('pos/search-items/', pos_views.pos_search_items, name='pos_search_items'),
    path('pos/search-patients/', pos_views.pos_search_patients, name='pos_search_patients'),
    path('pos/create-transaction/', pos_views.pos_create_transaction, name='pos_create_transaction'),
    
    # Transaction Management
    path('pos/transactions/', pos_views.PoSTransactionListView.as_view(), name='pos_transaction_list'),
    path('pos/transaction/<uuid:pk>/', pos_views.PoSTransactionDetailView.as_view(), name='pos_transaction_detail'),
    path('pos/transaction/<uuid:pk>/receipt/', pos_views.pos_transaction_receipt, name='pos_transaction_receipt'),
    
    # Item Management
    path('pos/items/', pos_views.PoSItemListView.as_view(), name='pos_item_list'),
    path('pos/items/add/', pos_views.PoSItemCreateView.as_view(), name='pos_item_create'),
    
    # Reports
    path('pos/daily-report/', pos_views.pos_daily_report, name='pos_daily_report'),
    
    # Day Close
    path('pos/close-day/', pos_views.pos_close_day, name='pos_close_day'),
    path('pos/day-close/<int:pk>/', pos_views.PoSDayCloseDetailView.as_view(), name='pos_day_close_detail'),
]
