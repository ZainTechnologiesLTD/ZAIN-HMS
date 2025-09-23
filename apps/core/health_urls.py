# apps/core/health_urls.py
from django.urls import path
from . import health

app_name = 'health'

urlpatterns = [
    path('', health.health_check, name='health_check'),
    path('ready/', health.readiness_check, name='readiness_check'),
    path('live/', health.liveness_check, name='liveness_check'),
]
