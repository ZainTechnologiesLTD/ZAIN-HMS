# billing/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BillViewSet, BillListView, BillDetailView, BillCreateView, billing_dashboard, 
    export_bills, bill_edit, bill_print, record_payment
)
from django.views.generic import TemplateView

router = DefaultRouter()
router.register(r'bills', BillViewSet)

app_name = 'billing'
urlpatterns = [
    path('', billing_dashboard, name='dashboard'),  # Main dashboard view
    path('list/', BillListView.as_view(), name='bill_list'),  # Bills list
    path('create/', BillCreateView.as_view(), name='create'),  # Create bill
    path('bill/<uuid:pk>/', BillDetailView.as_view(), name='bill_detail'),  # Bill detail
    path('bill/<uuid:pk>/edit/', bill_edit, name='bill_edit'),  # Edit bill
    path('bill/<uuid:pk>/print/', bill_print, name='bill_print'),  # Print bill
    path('export/', export_bills, name='export'),  # Export bills
    path('record-payment/', record_payment, name='record_payment'),  # Record payment
    path('api/', include(router.urls)),  # API endpoints
    path('quick_invoice/', BillViewSet.as_view({'get': 'quick_invoice'}), name='quick_invoice'),
    path('create_quick_invoice/', BillViewSet.as_view({'post': 'create_quick_invoice'}), name='create_quick_invoice'),
    
    # AI-Enhanced Billing URLs
    path('', include('apps.billing.ai_urls')),  # Include AI billing features
    
    # Point of Sale URLs
    path('', include('apps.billing.pos_urls')),  # Include PoS features
]