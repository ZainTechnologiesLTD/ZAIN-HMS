# Django Management Command for Maintenance Mode
# apps/core/management/commands/maintenance_mode.py

import os
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Enable or disable maintenance mode'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['on', 'off'],
            help='Turn maintenance mode on or off',
        )

    def handle(self, *args, **options):
        action = options['action']
        maintenance_file = os.path.join(settings.BASE_DIR, '.maintenance')
        
        if action == 'on':
            # Create maintenance file
            with open(maintenance_file, 'w') as f:
                f.write('MAINTENANCE MODE ENABLED\n')
                f.write('System is under maintenance. Please try again later.\n')
            
            self.stdout.write(
                self.style.WARNING('Maintenance mode enabled')
            )
            
        elif action == 'off':
            # Remove maintenance file
            if os.path.exists(maintenance_file):
                os.remove(maintenance_file)
                self.stdout.write(
                    self.style.SUCCESS('Maintenance mode disabled')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('Maintenance mode was not enabled')
                )