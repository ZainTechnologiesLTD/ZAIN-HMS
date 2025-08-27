from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('recent_list', views.recent_notifications, name='recent_list'),
    path('all/', views.all_notifications, name='all'),
]