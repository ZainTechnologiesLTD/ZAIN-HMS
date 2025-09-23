# ZAIN HMS Performance Monitoring and Caching Utils

from django.core.cache import cache
from django.db import connection
from django.conf import settings
from functools import wraps
import time
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger('zain_hms.performance')

class PerformanceMonitor:
    """Monitor and optimize database performance"""
    
    @staticmethod
    def log_slow_queries(func):
        """Decorator to log slow database queries"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            
            # Log queries that take longer than 1 second
            if end_time - start_time > 1.0:
                logger.warning(f"Slow query in {func.__name__}: {end_time - start_time:.2f}s")
                
            return result
        return wrapper
    
    @staticmethod
    def get_db_stats() -> Dict[str, Any]:
        """Get database performance statistics"""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_live_tup as live_tuples,
                    n_dead_tup as dead_tuples,
                    last_vacuum,
                    last_autovacuum,
                    last_analyze,
                    last_autoanalyze
                FROM pg_stat_user_tables 
                WHERE schemaname = 'public'
                ORDER BY n_live_tup DESC;
            """)
            
            stats = []
            for row in cursor.fetchall():
                stats.append({
                    'table': f"{row[0]}.{row[1]}",
                    'inserts': row[2],
                    'updates': row[3],
                    'deletes': row[4],
                    'live_tuples': row[5],
                    'dead_tuples': row[6],
                    'last_vacuum': row[7],
                    'last_autovacuum': row[8],
                    'last_analyze': row[9],
                    'last_autoanalyze': row[10]
                })
            
            return stats

class CacheManager:
    """Advanced caching utilities for ZAIN HMS"""
    
    # Cache timeouts in seconds
    CACHE_TIMEOUTS = {
        'dashboard_stats': 300,      # 5 minutes
        'patient_list': 600,         # 10 minutes
        'doctor_schedule': 900,      # 15 minutes
        'system_config': 3600,       # 1 hour
        'reports': 1800,             # 30 minutes
        'analytics': 900,            # 15 minutes
    }
    
    @classmethod
    def get_cache_key(cls, prefix: str, *args) -> str:
        """Generate standardized cache keys"""
        key_parts = [str(arg) for arg in args if arg is not None]
        return f"zain_hms:{prefix}:{':'.join(key_parts)}"
    
    @classmethod
    def cache_result(cls, cache_type: str, key_parts: list, timeout: Optional[int] = None):
        """Decorator for caching function results"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = cls.get_cache_key(cache_type, *key_parts)
                
                # Try to get from cache
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for {cache_key}")
                    return cached_result
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                cache_timeout = timeout or cls.CACHE_TIMEOUTS.get(cache_type, 300)
                cache.set(cache_key, result, cache_timeout)
                logger.debug(f"Cache set for {cache_key} (timeout: {cache_timeout}s)")
                
                return result
            return wrapper
        return decorator
    
    @classmethod
    def invalidate_pattern(cls, pattern: str):
        """Invalidate cache keys matching a pattern"""
        try:
            from django_redis import get_redis_connection
            redis_conn = get_redis_connection("default")
            keys = redis_conn.keys(f"zain_hms:{pattern}:*")
            if keys:
                redis_conn.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache keys matching pattern: {pattern}")
        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}")
    
    @classmethod
    def clear_user_cache(cls, user_id: int):
        """Clear all cache entries for a specific user"""
        patterns = ['dashboard_stats', 'patient_list', 'appointments']
        for pattern in patterns:
            cls.invalidate_pattern(f"{pattern}:user_{user_id}")

class DatabaseOptimizer:
    """Database query optimization utilities"""
    
    @staticmethod
    def optimize_queryset(queryset, select_related_fields=None, prefetch_related_fields=None):
        """Optimize queryset with select_related and prefetch_related"""
        if select_related_fields:
            queryset = queryset.select_related(*select_related_fields)
        
        if prefetch_related_fields:
            queryset = queryset.prefetch_related(*prefetch_related_fields)
        
        return queryset
    
    @staticmethod
    def bulk_create_optimized(model_class, objects, batch_size=1000, ignore_conflicts=False):
        """Optimized bulk create with batching"""
        total_created = 0
        for i in range(0, len(objects), batch_size):
            batch = objects[i:i + batch_size]
            created = model_class.objects.bulk_create(
                batch, 
                ignore_conflicts=ignore_conflicts,
                batch_size=batch_size
            )
            total_created += len(created)
            
        return total_created

class PerformanceMiddleware:
    """Middleware to monitor request performance"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        
        response = self.get_response(request)
        
        # Calculate request duration
        duration = time.time() - start_time
        
        # Log slow requests (> 2 seconds)
        if duration > 2.0:
            logger.warning(
                f"Slow request: {request.method} {request.path} "
                f"took {duration:.2f}s from {request.META.get('REMOTE_ADDR')}"
            )
        
        # Add performance header for development
        if settings.DEBUG:
            response['X-Response-Time'] = f"{duration:.3f}s"
        
        return response

# Cache warming functions
def warm_dashboard_cache():
    """Pre-warm dashboard cache with frequently accessed data"""
    from apps.patients.models import Patient
    from apps.appointments.models import Appointment
    from apps.doctors.models import Doctor
    
    logger.info("Warming dashboard cache...")
    
    # Cache counts
    cache.set('zain_hms:dashboard:patient_count', Patient.objects.count(), 3600)
    cache.set('zain_hms:dashboard:appointment_count', Appointment.objects.count(), 3600)
    cache.set('zain_hms:dashboard:doctor_count', Doctor.objects.count(), 3600)
    
    # Cache today's appointments
    today = datetime.now().date()
    today_appointments = Appointment.objects.filter(
        appointment_date=today
    ).select_related('patient', 'doctor').count()
    cache.set('zain_hms:dashboard:today_appointments', today_appointments, 1800)
    
    logger.info("Dashboard cache warmed successfully")

def warm_system_cache():
    """Warm system-wide cache"""
    from apps.core.models import SystemConfiguration
    
    logger.info("Warming system cache...")
    
    # Cache system configuration
    try:
        config = SystemConfiguration.objects.first()
        if config:
            cache.set('zain_hms:system:config', config, 3600)
    except Exception as e:
        logger.error(f"Failed to cache system config: {e}")
    
    logger.info("System cache warmed successfully")