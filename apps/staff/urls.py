# apps/staff/urls.py
from django.urls import path
from . import views

app_name = 'staff'

urlpatterns = [
    # Staff Management Views
    path('', views.StaffListView.as_view(), name='staff_list'),
    path('create/', views.StaffCreateView.as_view(), name='staff_create'),
    path('<uuid:pk>/', views.StaffDetailView.as_view(), name='staff_detail'),
    path('<uuid:pk>/update/', views.StaffUpdateView.as_view(), name='staff_update'),
    
    # User Management for Staff
    path('<uuid:pk>/create-user/', views.CreateUserForStaffView.as_view(), name='create_user_for_staff'),
    path('<uuid:pk>/link-user/', views.LinkStaffUserView.as_view(), name='link_user'),
    path('<uuid:pk>/unlink-user/', views.unlink_staff_user, name='unlink_user'),
    
    # Filter Views
    path('without-users/', views.StaffWithoutUsersView.as_view(), name='staff_without_users'),
    path('by-role/<str:role>/', views.StaffByRoleView.as_view(), name='staff_by_role'),
]
