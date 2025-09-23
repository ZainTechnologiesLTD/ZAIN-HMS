# apps/laboratory/urls.py
from django.urls import path
from . import views

app_name = 'laboratory'

urlpatterns = [
    # Dashboard
    path('', views.laboratory_dashboard, name='dashboard'),
    
    # Test Definitions
    path('tests/', views.LabTestListView.as_view(), name='lab_test_list'),
    path('tests/create/', views.LabTestCreateView.as_view(), name='lab_test_create'),
    path('tests/<uuid:pk>/', views.LabTestDetailView.as_view(), name='lab_test_detail'),
    path('tests/<uuid:pk>/update/', views.LabTestUpdateView.as_view(), name='lab_test_update'),
    path('tests/<uuid:pk>/delete/', views.LabTestDeleteView.as_view(), name='lab_test_delete'),
    
    # Lab Sections
    path('sections/', views.LabSectionListView.as_view(), name='lab_section_list'),
    path('sections/create/', views.LabSectionCreateView.as_view(), name='lab_section_create'),
    
    # Lab Orders
    path('orders/', views.LabOrderListView.as_view(), name='lab_order_list'),
    path('orders/create/', views.LabOrderCreateView.as_view(), name='lab_order_create'),
    path('orders/<uuid:pk>/', views.LabOrderDetailView.as_view(), name='lab_order_detail'),
    
    # Sample Collection
    path('order-items/<uuid:pk>/collect-sample/', views.SampleCollectionView.as_view(), name='collect_sample'),
    
    # Results
    path('results/create/<uuid:order_item_id>/', views.LabResultCreateView.as_view(), name='lab_result_create'),
    
    # Legacy redirects
    path('diagnostic-list/', views.diagnostic_list, name='diagnostic_list'),
    path('lab-tests/', views.lab_test_list, name='lab_test_list_legacy'),
]
