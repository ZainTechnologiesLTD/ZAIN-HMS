# apps/core/management/commands/backup_system.py
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from apps.core.backup import BackupManager
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Create system backup (database and media files)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--database-only',
            action='store_true',
            help='Backup only the database',
        )
        parser.add_argument(
            '--media-only',
            action='store_true',
            help='Backup only media files',
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Cleanup old backups after creating new ones',
        )
        parser.add_argument(
            '--keep-days',
            type=int,
            default=30,
            help='Number of days to keep old backups (default: 30)',
        )
    
    def handle(self, *args, **options):
        backup_manager = BackupManager()
        
        try:
            # Create backups
            if not options['media_only']:
                self.stdout.write('Creating database backup...')
                db_backup = backup_manager.backup_database()
                self.stdout.write(
                    self.style.SUCCESS(f'Database backup created: {db_backup}')
                )
            
            if not options['database_only']:
                self.stdout.write('Creating media backup...')
                media_backup = backup_manager.backup_media()
                self.stdout.write(
                    self.style.SUCCESS(f'Media backup created: {media_backup}')
                )
            
            # Cleanup old backups if requested
            if options['cleanup']:
                self.stdout.write('Cleaning up old backups...')
                backup_manager.cleanup_old_backups(keep_days=options['keep_days'])
                self.stdout.write(self.style.SUCCESS('Cleanup completed'))
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            raise CommandError(f'Backup failed: {e}')
        
        self.stdout.write(self.style.SUCCESS('Backup completed successfully'))
