from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('recent_list', views.recent_notifications, name='recent_list'),
    path('all/', views.all_notifications, name='all'),
    path('create/', views.create_notification, name='create'),
    path('create-bulk/', views.create_bulk_notification, name='create_bulk'),
]