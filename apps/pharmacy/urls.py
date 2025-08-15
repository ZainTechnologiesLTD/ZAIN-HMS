# pharmaceuticals/urls.py
from django.urls import path
from .views import bill_list_view, bill_detail_view


app_name = 'pharmaceutical'  # Namespace registration

urlpatterns = [
    path('bills/', bill_list_view, name='medicine_list'),  # Matches 'medicine-list'
    path('bills/<int:bill_id>/', bill_detail_view, name='bill_detail'),
]
