# ipd/urls.py
from django.urls import path
from . import views

app_name = 'ipd'  # This is important for namespace

urlpatterns = [
    path('', views.IPDListView.as_view(), name='ipd_list'),
    path('create/', views.IPDCreateView.as_view(), name='ipd_create'),
    path('<int:pk>/', views.IPDDetailView.as_view(), name='ipd_detail'),
    path('<int:pk>/update/', views.IPDUpdateView.as_view(), name='ipd_update'),
    path('<int:pk>/delete/', views.IPDDeleteView.as_view(), name='ipd_delete'),
]