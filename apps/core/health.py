# apps/core/health.py
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from django.db import connection
from django.core.cache import cache
from django.conf import settings
import psutil
import os
import time
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@never_cache
@require_http_methods(["GET"])
def health_check(request):
    """Comprehensive health check endpoint"""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'checks': {}
    }
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            health_status['checks']['database'] = {
                'status': 'healthy',
                'response_time_ms': 0  # Will be updated
            }
    except Exception as e:
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_status['status'] = 'unhealthy'
    
    # Cache check
    try:
        cache_key = 'health_check_test'
        cache.set(cache_key, 'test', 60)
        cached_value = cache.get(cache_key)
        
        if cached_value == 'test':
            health_status['checks']['cache'] = {'status': 'healthy'}
        else:
            raise Exception("Cache value mismatch")
    except Exception as e:
        health_status['checks']['cache'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_status['status'] = 'unhealthy'
    
    # Disk space check
    try:
        disk_usage = psutil.disk_usage('/')
        disk_percent = (disk_usage.used / disk_usage.total) * 100
        
        health_status['checks']['disk_space'] = {
            'status': 'healthy' if disk_percent < 90 else 'warning',
            'usage_percent': round(disk_percent, 2),
            'free_gb': round(disk_usage.free / (1024**3), 2)
        }
        
        if disk_percent >= 95:
            health_status['status'] = 'unhealthy'
    except Exception as e:
        health_status['checks']['disk_space'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
    
    # Memory check
    try:
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        health_status['checks']['memory'] = {
            'status': 'healthy' if memory_percent < 85 else 'warning',
            'usage_percent': memory_percent,
            'available_gb': round(memory.available / (1024**3), 2)
        }
        
        if memory_percent >= 95:
            health_status['status'] = 'unhealthy'
    except Exception as e:
        health_status['checks']['memory'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
    
    # CPU check
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        
        health_status['checks']['cpu'] = {
            'status': 'healthy' if cpu_percent < 80 else 'warning',
            'usage_percent': cpu_percent
        }
        
        if cpu_percent >= 95:
            health_status['status'] = 'unhealthy'
    except Exception as e:
        health_status['checks']['cpu'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
    
    # Determine HTTP status code
    if health_status['status'] == 'healthy':
        status_code = 200
    elif health_status['status'] == 'warning':
        status_code = 200  # Still healthy but with warnings
    else:
        status_code = 503  # Service unavailable
    
    return JsonResponse(health_status, status=status_code)


@never_cache
@require_http_methods(["GET"])
def readiness_check(request):
    """Readiness check for Kubernetes/Docker deployments"""
    readiness_status = {
        'ready': True,
        'timestamp': datetime.now().isoformat(),
        'checks': {}
    }
    
    # Critical database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM django_migrations")
            readiness_status['checks']['database'] = {'ready': True}
    except Exception as e:
        readiness_status['checks']['database'] = {
            'ready': False,
            'error': str(e)
        }
        readiness_status['ready'] = False
    
    # Cache availability
    try:
        cache.set('readiness_test', 'ready', 10)
        readiness_status['checks']['cache'] = {'ready': True}
    except Exception as e:
        readiness_status['checks']['cache'] = {
            'ready': False,
            'error': str(e)
        }
        readiness_status['ready'] = False
    
    status_code = 200 if readiness_status['ready'] else 503
    return JsonResponse(readiness_status, status=status_code)


@never_cache
@require_http_methods(["GET"])
def liveness_check(request):
    """Liveness check for Kubernetes/Docker deployments"""
    return JsonResponse({
        'alive': True,
        'timestamp': datetime.now().isoformat(),
        'uptime_seconds': time.time() - psutil.boot_time()
    })


class SystemMonitor:
    """System monitoring and alerting"""
    
    def __init__(self):
        self.metrics_cache_key = 'system_metrics'
        self.alert_thresholds = {
            'cpu_percent': 80,
            'memory_percent': 85,
            'disk_percent': 90,
            'response_time_ms': 1000
        }
    
    def collect_metrics(self):
        """Collect system metrics"""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'cpu': {
                'percent': psutil.cpu_percent(interval=1),
                'count': psutil.cpu_count(),
                'load_avg': os.getloadavg() if hasattr(os, 'getloadavg') else None
            },
            'memory': {
                'percent': psutil.virtual_memory().percent,
                'available_gb': round(psutil.virtual_memory().available / (1024**3), 2),
                'total_gb': round(psutil.virtual_memory().total / (1024**3), 2)
            },
            'disk': {
                'percent': round((psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100, 2),
                'free_gb': round(psutil.disk_usage('/').free / (1024**3), 2),
                'total_gb': round(psutil.disk_usage('/').total / (1024**3), 2)
            }
        }
        
        # Database response time
        try:
            start_time = time.time()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            metrics['database'] = {
                'response_time_ms': round((time.time() - start_time) * 1000, 2),
                'status': 'healthy'
            }
        except Exception as e:
            metrics['database'] = {
                'response_time_ms': None,
                'status': 'unhealthy',
                'error': str(e)
            }
        
        # Cache metrics to avoid frequent system calls
        cache.set(self.metrics_cache_key, metrics, 60)  # Cache for 1 minute
        
        return metrics
    
    def get_cached_metrics(self):
        """Get cached metrics or collect new ones"""
        metrics = cache.get(self.metrics_cache_key)
        if not metrics:
            metrics = self.collect_metrics()
        return metrics
    
    def check_alerts(self):
        """Check for alert conditions"""
        metrics = self.get_cached_metrics()
        alerts = []
        
        # CPU alert
        if metrics['cpu']['percent'] > self.alert_thresholds['cpu_percent']:
            alerts.append({
                'type': 'cpu_high',
                'message': f"High CPU usage: {metrics['cpu']['percent']:.1f}%",
                'severity': 'warning' if metrics['cpu']['percent'] < 95 else 'critical'
            })
        
        # Memory alert
        if metrics['memory']['percent'] > self.alert_thresholds['memory_percent']:
            alerts.append({
                'type': 'memory_high',
                'message': f"High memory usage: {metrics['memory']['percent']:.1f}%",
                'severity': 'warning' if metrics['memory']['percent'] < 95 else 'critical'
            })
        
        # Disk alert
        if metrics['disk']['percent'] > self.alert_thresholds['disk_percent']:
            alerts.append({
                'type': 'disk_full',
                'message': f"Low disk space: {metrics['disk']['percent']:.1f}% used",
                'severity': 'warning' if metrics['disk']['percent'] < 95 else 'critical'
            })
        
        # Database response time alert
        if (metrics['database']['response_time_ms'] and 
            metrics['database']['response_time_ms'] > self.alert_thresholds['response_time_ms']):
            alerts.append({
                'type': 'database_slow',
                'message': f"Slow database response: {metrics['database']['response_time_ms']:.1f}ms",
                'severity': 'warning'
            })
        
        return alerts
    
    def get_system_status(self):
        """Get overall system status"""
        metrics = self.get_cached_metrics()
        alerts = self.check_alerts()
        
        # Determine overall status
        if any(alert['severity'] == 'critical' for alert in alerts):
            status = 'critical'
        elif any(alert['severity'] == 'warning' for alert in alerts):
            status = 'warning'
        else:
            status = 'healthy'
        
        return {
            'status': status,
            'metrics': metrics,
            'alerts': alerts,
            'last_updated': metrics['timestamp']
        }
