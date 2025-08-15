from django.urls import path
from .views import LabTestViewSet, LabResultViewSet, diagnostic_list, lab_result_list

app_name = 'diagnostics'

urlpatterns = [
    path('', diagnostic_list, name='diagnostic_list'),  # New URL for diagnostic-list
    path('lab_tests/<int:lab_test_id>/results/', lab_result_list, name='lab_result_list'),
    path('lab_tests/create/', LabTestViewSet.as_view({'get': 'create', 'post': 'create'}), name='lab_test_create'),
    path('lab_tests/<int:pk>/update/', LabTestViewSet.as_view({'get': 'update', 'post': 'update'}), name='lab_test_update'),
    path('lab_tests/<int:pk>/delete/', LabTestViewSet.as_view({'get': 'destroy', 'post': 'destroy'}), name='lab_test_delete'),
    path('lab_results/<int:pk>/update/', LabResultViewSet.as_view({'get': 'update', 'post': 'update'}), name='lab_result_update'),
    path('lab_results/<int:pk>/delete/', LabResultViewSet.as_view({'get': 'destroy', 'post': 'destroy'}), name='lab_result_delete'),
    path('lab_results/create/<int:lab_test_id>/', LabResultViewSet.as_view({'get': 'create', 'post': 'create'}), name='lab_result_create'),
]
