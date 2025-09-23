# Django Management Command for Cache Clearing
# apps/core/management/commands/clear_cache.py

from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.conf import settings
import redis


class Command(BaseCommand):
    help = 'Clear all Django caches'

    def add_arguments(self, parser):
        parser.add_arguments(
            '--cache-key',
            type=str,
            help='Clear specific cache key pattern',
        )

    def handle(self, *args, **options):
        cache_key = options.get('cache_key')
        
        try:
            if cache_key:
                # Clear specific cache pattern
                cache.delete_pattern(cache_key)
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully cleared cache pattern: {cache_key}')
                )
            else:
                # Clear all cache
                cache.clear()
                self.stdout.write(
                    self.style.SUCCESS('Successfully cleared all Django cache')
                )
                
            # Clear Redis cache if configured
            if hasattr(settings, 'CACHES') and 'redis' in str(settings.CACHES).lower():
                try:
                    # Get Redis connection details from Django settings
                    redis_config = settings.CACHES.get('default', {})
                    location = redis_config.get('LOCATION', 'redis://127.0.0.1:6379/1')
                    
                    # Parse Redis URL
                    if location.startswith('redis://'):
                        import urllib.parse
                        parsed = urllib.parse.urlparse(location)
                        host = parsed.hostname or '127.0.0.1'
                        port = parsed.port or 6379
                        db = int(parsed.path[1:]) if parsed.path and len(parsed.path) > 1 else 1
                        
                        # Connect to Redis and flush
                        r = redis.Redis(host=host, port=port, db=db)
                        r.flushdb()
                        self.stdout.write(
                            self.style.SUCCESS('Successfully cleared Redis cache')
                        )
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'Could not clear Redis cache: {e}')
                    )
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error clearing cache: {e}')
            )