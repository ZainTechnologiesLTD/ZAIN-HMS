from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
import time
import psutil
import logging

logger = logging.getLogger('zain_hms.performance')

class Command(BaseCommand):
    help = 'Monitor ZAIN HMS application performance'

    def add_arguments(self, parser):
        parser.add_argument(
            '--duration',
            type=int,
            default=60,
            help='Monitoring duration in seconds (default: 60)',
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=5,
            help='Monitoring interval in seconds (default: 5)',
        )

    def handle(self, *args, **options):
        duration = options['duration']
        interval = options['interval']
        
        self.stdout.write(
            self.style.SUCCESS(f'🔍 Starting performance monitoring for {duration}s')
        )
        
        start_time = time.time()
        iterations = 0
        
        while time.time() - start_time < duration:
            self._collect_metrics(iterations)
            time.sleep(interval)
            iterations += 1
        
        self.stdout.write(
            self.style.SUCCESS('✅ Performance monitoring completed')
        )

    def _collect_metrics(self, iteration):
        """Collect and display performance metrics"""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Database metrics
            with connection.cursor() as cursor:
                # Active connections
                cursor.execute("""
                    SELECT count(*) FROM pg_stat_activity 
                    WHERE state = 'active' AND pid != pg_backend_pid()
                """)
                active_connections = cursor.fetchone()[0]
                
                # Database size
                cursor.execute("""
                    SELECT pg_size_pretty(pg_database_size(current_database()))
                """)
                db_size = cursor.fetchone()[0]
                
                # Cache hit ratio
                cursor.execute("""
                    SELECT 
                        round(
                            (sum(blks_hit) / (sum(blks_hit) + sum(blks_read))) * 100, 
                            2
                        ) as cache_hit_ratio
                    FROM pg_stat_database 
                    WHERE datname = current_database()
                """)
                cache_hit_ratio = cursor.fetchone()[0] or 0
            
            # Display metrics
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            
            self.stdout.write(f"""
🕐 {timestamp} (Sample #{iteration + 1})
┌─ System Performance
│  CPU: {cpu_percent}% | Memory: {memory.percent}% | Disk: {disk.percent}%
├─ Database Performance  
│  Connections: {active_connections} | Size: {db_size} | Cache Hit: {cache_hit_ratio}%
└─ Status: {'🟢 GOOD' if cpu_percent < 80 and memory.percent < 80 else '🟡 WARNING' if cpu_percent < 95 else '🔴 CRITICAL'}
            """)
            
            # Log performance warnings
            if cpu_percent > 90:
                logger.warning(f"High CPU usage: {cpu_percent}%")
            
            if memory.percent > 90:
                logger.warning(f"High memory usage: {memory.percent}%")
            
            if cache_hit_ratio < 90:
                logger.warning(f"Low database cache hit ratio: {cache_hit_ratio}%")
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error collecting metrics: {e}")
            )
            logger.error(f"Performance monitoring error: {e}")