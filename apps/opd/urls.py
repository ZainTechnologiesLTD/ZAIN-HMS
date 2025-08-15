# opd/urls.py
from django.urls import path
from . import views

app_name = 'opd'

urlpatterns = [
    # Main CRUD URLs
    path('', views.OPDListView.as_view(), name='opd_list'),
    path('create/', views.OPDCreateView.as_view(), name='opd_create'),
    path('<int:pk>/', views.OPDDetailView.as_view(), name='opd_detail'),
    path('<int:pk>/update/', views.OPDUpdateView.as_view(), name='opd_update'),
    path('<int:pk>/delete/', views.OPDDeleteView.as_view(), name='opd_delete'),
    
    # HTMX URLs
    path('search/', views.opd_search, name='opd-search'),
    path('<int:pk>/toggle_payment/', views.toggle_payment_status, name='toggle_payment'),
]
