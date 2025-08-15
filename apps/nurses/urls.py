from django.urls import path
from . import views

app_name = 'nurses'

urlpatterns = [
    # Nurse URLs
    path('', views.NurseListView.as_view(), name='nurse_list'),
    path('create/', views.NurseCreateView.as_view(), name='nurse_create'),
    path('<int:pk>/', views.NurseDetailView.as_view(), name='nurse_detail'),
    path('<int:pk>/update/', views.NurseUpdateView.as_view(), name='nurse_update'),
    path('<int:pk>/delete/', views.NurseDeleteView.as_view(), name='nurse_delete'),
    
    # Schedule URLs
    path('<int:nurse_id>/schedule/create/', views.ScheduleCreateView.as_view(), name='schedule_create'),
    path('schedule/<int:pk>/update/', views.ScheduleUpdateView.as_view(), name='schedule_update'),
    
    # Leave Management URLs
    path('<int:nurse_id>/leave/request/', views.leave_request, name='leave_request'),
    path('leave/<int:leave_id>/approve/', views.approve_leave, name='leave_approve'),
    path('leave/<int:leave_id>/reject/', views.reject_leave, name='leave_reject'),
]