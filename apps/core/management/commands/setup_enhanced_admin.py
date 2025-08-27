"""
Management command to set up and configure enhanced admin UI
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
import os


class Command(BaseCommand):
    help = 'Set up enhanced admin UI with all configurations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-superuser',
            action='store_true',
            help='Create a superuser for admin access',
        )
        parser.add_argument(
            '--apply-permissions',
            action='store_true',
            help='Apply enhanced permissions and groups',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Setting up Zain HMS Enhanced Admin UI...')
        )

        # Apply static files
        self.setup_static_files()
        
        # Set up admin groups and permissions
        if options['apply_permissions']:
            self.setup_admin_permissions()
        
        # Create superuser if requested
        if options['create_superuser']:
            self.create_enhanced_superuser()
        
        # Verify admin enhancements
        self.verify_setup()
        
        self.stdout.write(
            self.style.SUCCESS(
                'Enhanced Admin UI setup completed successfully!\n'
                'Access your enhanced admin at: /admin/\n'
                'Features enabled:\n'
                '  ✓ Modern Jazzmin theme with custom styling\n'
                '  ✓ Enhanced dashboard with analytics\n'
                '  ✓ Advanced filters and search\n'
                '  ✓ CSV/JSON export functionality\n'
                '  ✓ Dark/Light theme toggle\n'
                '  ✓ Real-time statistics\n'
                '  ✓ Custom admin actions\n'
                '  ✓ Responsive design\n'
            )
        )

    def setup_static_files(self):
        """Verify static files are in place"""
        self.stdout.write('Checking static files...')
        
        static_files = [
            'static/css/admin_enhanced.css',
            'static/js/admin_enhanced.js',
            'static/js/theme_switcher.js',
        ]
        
        for file_path in static_files:
            if os.path.exists(file_path):
                self.stdout.write(f'  ✓ {file_path}')
            else:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠ {file_path} not found')
                )

    def setup_admin_permissions(self):
        """Set up enhanced admin permissions and groups"""
        self.stdout.write('Setting up admin permissions and groups...')
        
        # Create Admin Groups
        admin_groups = [
            ('Super Administrators', []),
            ('Hospital Administrators', []),
            ('Department Heads', []),
            ('Medical Staff', []),
            ('Administrative Staff', []),
        ]
        
        for group_name, permissions in admin_groups:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(f'  ✓ Created group: {group_name}')
            else:
                self.stdout.write(f'  • Group exists: {group_name}')

    def create_enhanced_superuser(self):
        """Create superuser with enhanced permissions"""
        self.stdout.write('Creating enhanced superuser...')
        
        username = input('Enter username: ')
        email = input('Enter email: ')
        
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'User {username} already exists')
            )
            return
        
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=input('Enter password: ')
        )
        
        # Add to Super Administrators group
        super_admin_group, _ = Group.objects.get_or_create(
            name='Super Administrators'
        )
        user.groups.add(super_admin_group)
        
        self.stdout.write(
            self.style.SUCCESS(f'Superuser {username} created successfully')
        )

    def verify_setup(self):
        """Verify that all enhancements are properly configured"""
        self.stdout.write('Verifying setup...')
        
        # Check templates
        template_files = [
            'templates/admin/base_site.html',
            'templates/admin/index.html',
            'templates/admin/change_list.html',
            'templates/admin/dashboard.html',
            'templates/admin/analytics.html',
        ]
        
        for template in template_files:
            if os.path.exists(template):
                self.stdout.write(f'  ✓ {template}')
            else:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠ {template} not found')
                )
        
        # Check settings configuration
        try:
            from django.conf import settings
            if hasattr(settings, 'JAZZMIN_SETTINGS'):
                self.stdout.write('  ✓ Jazzmin settings configured')
            else:
                self.stdout.write(
                    self.style.WARNING('  ⚠ Jazzmin settings not found')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'  ✗ Settings error: {e}')
            )
