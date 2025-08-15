# billing/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BillViewSet

router = DefaultRouter()
router.register(r'bills', BillViewSet)

app_name = 'billing'
urlpatterns = [
    path('', include(router.urls)),
    path('quick_invoice/', BillViewSet.as_view({'get': 'quick_invoice'}), name='quick_invoice'),
    path('create_quick_invoice/', BillViewSet.as_view({'post': 'create_quick_invoice'}), name='create_quick_invoice'),
]