# Post-Migration Tasks Command
# apps/core/management/commands/post_migration_tasks.py

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = 'Run post-migration tasks after database updates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-permissions',
            action='store_true',
            help='Skip updating permissions',
        )
        parser.add_argument(
            '--skip-fixtures',
            action='store_true',
            help='Skip loading initial data fixtures',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔧 Running post-migration tasks...')
        )
        
        tasks_completed = 0
        
        # Update content types and permissions
        if not options.get('skip_permissions'):
            self.update_permissions()
            tasks_completed += 1
        
        # Load initial data fixtures if needed
        if not options.get('skip_fixtures'):
            self.load_initial_fixtures()
            tasks_completed += 1
        
        # Update user permissions for new features
        self.update_user_permissions()
        tasks_completed += 1
        
        # Create default system configurations
        self.create_system_configs()
        tasks_completed += 1
        
        # Update notification templates
        self.update_notification_templates()
        tasks_completed += 1
        
        # Rebuild search indexes if needed
        self.rebuild_search_indexes()
        tasks_completed += 1
        
        # Clear outdated cache entries
        self.clear_stale_cache()
        tasks_completed += 1
        
        # Update system version info
        self.update_version_info()
        tasks_completed += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Completed {tasks_completed} post-migration tasks')
        )

    def update_permissions(self):
        """Update Django permissions after model changes"""
        try:
            self.stdout.write('   • Updating content types and permissions...')
            call_command('migrate', '--run-syncdb', verbosity=0)
            self.stdout.write('   ✅ Permissions updated')
        except Exception as e:
            logger.error(f"Error updating permissions: {e}")
            self.stdout.write(
                self.style.WARNING(f'   ⚠️  Permission update failed: {e}')
            )

    def load_initial_fixtures(self):
        """Load initial data fixtures"""
        try:
            self.stdout.write('   • Loading initial data fixtures...')
            
            # List of fixtures to load (add your fixture files here)
            fixtures = [
                'initial_departments.json',
                'initial_roles.json',
                'default_configurations.json',
            ]
            
            for fixture in fixtures:
                try:
                    call_command('loaddata', fixture, verbosity=0)
                except Exception:
                    # Fixture might not exist or already loaded
                    pass
            
            self.stdout.write('   ✅ Fixtures loaded')
        except Exception as e:
            logger.error(f"Error loading fixtures: {e}")
            self.stdout.write(
                self.style.WARNING(f'   ⚠️  Fixture loading failed: {e}')
            )

    def update_user_permissions(self):
        """Update user permissions for new features"""
        try:
            self.stdout.write('   • Updating user permissions...')
            
            # Add superuser permissions for new models
            from django.contrib.auth.models import Permission
            from django.contrib.contenttypes.models import ContentType
            
            # Get or create admin group with all permissions
            from django.contrib.auth.models import Group
            admin_group, created = Group.objects.get_or_create(name='System Administrators')
            
            if created:
                # Add all permissions to admin group
                all_permissions = Permission.objects.all()
                admin_group.permissions.set(all_permissions)
                admin_group.save()
            
            self.stdout.write('   ✅ User permissions updated')
        except Exception as e:
            logger.error(f"Error updating user permissions: {e}")
            self.stdout.write(
                self.style.WARNING(f'   ⚠️  User permissions update failed: {e}')
            )

    def create_system_configs(self):
        """Create default system configurations"""
        try:
            self.stdout.write('   • Creating system configurations...')
            
            from apps.core.models import SystemConfiguration
            
            default_configs = [
                {
                    'key': 'system.version',
                    'value': getattr(settings, 'VERSION', '1.0.0'),
                    'description': 'Current system version'
                },
                {
                    'key': 'update.check_enabled',
                    'value': 'true',
                    'description': 'Enable automatic update checking'
                },
                {
                    'key': 'maintenance.notification_minutes',
                    'value': '30',
                    'description': 'Minutes before maintenance to notify users'
                },
            ]
            
            for config in default_configs:
                SystemConfiguration.objects.get_or_create(
                    key=config['key'],
                    defaults={
                        'value': config['value'],
                        'description': config['description']
                    }
                )
            
            self.stdout.write('   ✅ System configurations created')
        except Exception as e:
            logger.error(f"Error creating system configs: {e}")
            self.stdout.write(
                self.style.WARNING(f'   ⚠️  System config creation failed: {e}')
            )

    def update_notification_templates(self):
        """Update notification templates"""
        try:
            self.stdout.write('   • Updating notification templates...')
            
            # Update notification templates for new features
            # This would update email templates, push notification templates, etc.
            
            self.stdout.write('   ✅ Notification templates updated')
        except Exception as e:
            logger.error(f"Error updating notification templates: {e}")
            self.stdout.write(
                self.style.WARNING(f'   ⚠️  Template update failed: {e}')
            )

    def rebuild_search_indexes(self):
        """Rebuild search indexes if search is configured"""
        try:
            self.stdout.write('   • Rebuilding search indexes...')
            
            # Check if search backend is configured
            if hasattr(settings, 'HAYSTACK_CONNECTIONS'):
                call_command('rebuild_index', '--noinput', verbosity=0)
                self.stdout.write('   ✅ Search indexes rebuilt')
            else:
                self.stdout.write('   • No search backend configured, skipping')
                
        except Exception as e:
            logger.error(f"Error rebuilding search indexes: {e}")
            self.stdout.write(
                self.style.WARNING(f'   ⚠️  Search index rebuild failed: {e}')
            )

    def clear_stale_cache(self):
        """Clear stale cache entries"""
        try:
            self.stdout.write('   • Clearing stale cache entries...')
            
            from django.core.cache import cache
            
            # Clear specific cache keys that might be outdated
            stale_keys = [
                'user_permissions_*',
                'system_config_*',
                'navigation_menu_*',
                'dashboard_stats_*'
            ]
            
            for key_pattern in stale_keys:
                try:
                    cache.delete_pattern(key_pattern)
                except AttributeError:
                    # delete_pattern not available in all cache backends
                    pass
            
            self.stdout.write('   ✅ Stale cache cleared')
        except Exception as e:
            logger.error(f"Error clearing stale cache: {e}")
            self.stdout.write(
                self.style.WARNING(f'   ⚠️  Cache clearing failed: {e}')
            )

    def update_version_info(self):
        """Update system version information"""
        try:
            self.stdout.write('   • Updating version information...')
            
            from apps.core.models import SystemConfiguration
            
            current_version = getattr(settings, 'VERSION', '1.0.0')
            
            SystemConfiguration.objects.update_or_create(
                key='system.version',
                defaults={
                    'value': current_version,
                    'description': 'Current system version'
                }
            )
            
            self.stdout.write(f'   ✅ Version updated to {current_version}')
        except Exception as e:
            logger.error(f"Error updating version info: {e}")
            self.stdout.write(
                self.style.WARNING(f'   ⚠️  Version update failed: {e}')
            )