# ipd/urls.py
from django.urls import path
from . import views
from . import room_management

app_name = 'ipd'  # This is important for namespace

urlpatterns = [
    # IPD Record URLs
    path('', views.IPDListView.as_view(), name='ipd_list'),
    path('create/', views.IPDCreateView.as_view(), name='ipd_create'),
    path('<int:pk>/', views.IPDDetailView.as_view(), name='ipd_detail'),
    path('<int:pk>/update/', views.IPDUpdateView.as_view(), name='ipd_update'),
    path('<int:pk>/delete/', views.IPDDeleteView.as_view(), name='ipd_delete'),
    
    # Room Management URLs
    path('rooms/', room_management.RoomListView.as_view(), name='room_list'),
    path('rooms/create/', room_management.RoomCreateView.as_view(), name='room_create'),
    path('rooms/<int:pk>/update/', room_management.RoomUpdateView.as_view(), name='room_update'),
    path('rooms/<int:pk>/delete/', room_management.RoomDeleteView.as_view(), name='room_delete'),
    
    # Bed Management URLs
    path('beds/', room_management.BedListView.as_view(), name='bed_list'),
    path('beds/create/', room_management.BedCreateView.as_view(), name='bed_create'),
    path('beds/<int:pk>/update/', room_management.BedUpdateView.as_view(), name='bed_update'),
    path('beds/<int:pk>/delete/', room_management.BedDeleteView.as_view(), name='bed_delete'),
    
    # AJAX endpoints for search functionality
    path('ajax/search-patients/', views.ajax_search_patients, name='ajax_search_patients'),
    path('ajax/search-doctors/', views.ajax_search_doctors, name='ajax_search_doctors'),
    path('ajax/get-available-beds/', views.ajax_get_available_beds, name='ajax_get_available_beds'),
]