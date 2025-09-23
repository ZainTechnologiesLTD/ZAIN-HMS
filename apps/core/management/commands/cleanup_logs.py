# apps/core/management/commands/cleanup_logs.py
from django.core.management.base import BaseCommand
from django.conf import settings
from datetime import datetime, timedelta
from pathlib import Path
import os
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Cleanup old log files and activity logs'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to keep logs (default: 30)',
        )
        parser.add_argument(
            '--activity-logs',
            action='store_true',
            help='Also cleanup old activity logs from database',
        )
    
    def handle(self, *args, **options):
        days_to_keep = options['days']
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # Cleanup log files
        log_dir = getattr(settings, 'BASE_DIR', Path('.')) / 'logs'
        if log_dir.exists():
            files_deleted = 0
            for log_file in log_dir.rglob('*.log*'):
                if log_file.is_file():
                    file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if file_time < cutoff_date:
                        try:
                            log_file.unlink()
                            files_deleted += 1
                            self.stdout.write(f'Deleted: {log_file}')
                        except OSError as e:
                            self.stdout.write(
                                self.style.WARNING(f'Could not delete {log_file}: {e}')
                            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Deleted {files_deleted} old log files')
            )
        
        # Cleanup activity logs from database
        if options['activity_logs']:
            from apps.core.models import ActivityLog
            
            old_logs = ActivityLog.objects.filter(
                timestamp__lt=cutoff_date
            )
            count = old_logs.count()
            old_logs.delete()
            
            self.stdout.write(
                self.style.SUCCESS(f'Deleted {count} old activity log entries')
            )
        
        self.stdout.write(self.style.SUCCESS('Log cleanup completed'))
