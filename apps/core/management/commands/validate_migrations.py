# Migration Validator and Safety Checker
# apps/core/management/commands/validate_migrations.py

import os
import subprocess
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
from django.apps import apps
from django.conf import settings
import json


class Command(BaseCommand):
    help = 'Validate database migrations and check for potential issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without applying',
        )
        parser.add_argument(
            '--check-backward-compatibility',
            action='store_true',
            help='Check for backward compatibility issues',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        check_compatibility = options.get('check_backward_compatibility', False)
        
        self.stdout.write(
            self.style.SUCCESS('🔍 Starting migration validation...')
        )
        
        # Check pending migrations
        pending_migrations = self.get_pending_migrations()
        
        if not pending_migrations:
            self.stdout.write(
                self.style.SUCCESS('✅ No pending migrations found')
            )
            return
        
        self.stdout.write(
            self.style.WARNING(f'📋 Found {len(pending_migrations)} pending migrations:')
        )
        
        for migration in pending_migrations:
            self.stdout.write(f'   • {migration}')
        
        # Analyze migration safety
        self.analyze_migration_safety(pending_migrations)
        
        # Check for backward compatibility issues
        if check_compatibility:
            self.check_backward_compatibility(pending_migrations)
        
        # Estimate migration time
        estimated_time = self.estimate_migration_time(pending_migrations)
        if estimated_time:
            self.stdout.write(
                self.style.WARNING(f'⏱️  Estimated migration time: {estimated_time}')
            )
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS('🔍 Dry run completed. No changes were made.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('✅ Migration validation completed')
            )

    def get_pending_migrations(self):
        """Get list of pending migrations"""
        try:
            # Use Django's migration executor
            from django.db.migrations.executor import MigrationExecutor
            
            executor = MigrationExecutor(connection)
            plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
            
            return [f"{migration.app_label}.{migration.name}" for migration, backwards in plan if not backwards]
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error getting pending migrations: {e}')
            )
            return []

    def analyze_migration_safety(self, migrations):
        """Analyze migrations for potential issues"""
        self.stdout.write(
            self.style.SUCCESS('🔒 Analyzing migration safety...')
        )
        
        risky_operations = []
        
        for migration_name in migrations:
            try:
                app_label, migration_file = migration_name.split('.')
                migration_path = self.get_migration_file_path(app_label, migration_file)
                
                if migration_path and os.path.exists(migration_path):
                    with open(migration_path, 'r') as f:
                        content = f.read()
                        
                    # Check for risky operations
                    risky_patterns = {
                        'DROP TABLE': 'Table deletion detected',
                        'DROP COLUMN': 'Column deletion detected',
                        'ALTER TABLE': 'Table alteration detected',
                        'CREATE INDEX': 'Index creation (may lock table)',
                        'DROP INDEX': 'Index deletion detected',
                        'UNIQUE': 'Unique constraint addition',
                        'NOT NULL': 'NOT NULL constraint addition',
                    }
                    
                    for pattern, description in risky_patterns.items():
                        if pattern.lower() in content.lower():
                            risky_operations.append({
                                'migration': migration_name,
                                'operation': description,
                                'risk_level': self.assess_risk_level(pattern)
                            })
                            
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Could not analyze {migration_name}: {e}')
                )
        
        if risky_operations:
            self.stdout.write(
                self.style.ERROR('⚠️  Found potentially risky operations:')
            )
            for op in risky_operations:
                risk_color = self.style.ERROR if op['risk_level'] == 'HIGH' else self.style.WARNING
                self.stdout.write(
                    risk_color(f'   • {op["migration"]}: {op["operation"]} (Risk: {op["risk_level"]})')
                )
        else:
            self.stdout.write(
                self.style.SUCCESS('✅ No obviously risky operations detected')
            )

    def get_migration_file_path(self, app_label, migration_name):
        """Get the file path for a migration"""
        try:
            app_config = apps.get_app_config(app_label)
            migrations_dir = os.path.join(app_config.path, 'migrations')
            migration_file = f"{migration_name}.py"
            return os.path.join(migrations_dir, migration_file)
        except:
            return None

    def assess_risk_level(self, operation):
        """Assess risk level of migration operation"""
        high_risk = ['DROP TABLE', 'DROP COLUMN']
        medium_risk = ['ALTER TABLE', 'NOT NULL', 'UNIQUE']
        
        if operation in high_risk:
            return 'HIGH'
        elif operation in medium_risk:
            return 'MEDIUM'
        else:
            return 'LOW'

    def check_backward_compatibility(self, migrations):
        """Check for backward compatibility issues"""
        self.stdout.write(
            self.style.SUCCESS('🔄 Checking backward compatibility...')
        )
        
        # This would involve more complex analysis
        # For now, we'll provide basic guidance
        compatibility_warnings = [
            "Ensure old code can handle new database schema",
            "Check if any fields were renamed or removed",
            "Verify that new constraints don't break existing data",
            "Test rollback procedures before deployment"
        ]
        
        for warning in compatibility_warnings:
            self.stdout.write(
                self.style.WARNING(f'   ⚠️  {warning}')
            )

    def estimate_migration_time(self, migrations):
        """Estimate migration time based on operations"""
        # This is a rough estimation
        total_time = 0
        
        for migration in migrations:
            # Base time per migration
            total_time += 5  # seconds
            
            # Add time based on table size estimates
            # In a real implementation, you'd query actual table sizes
            total_time += 10  # additional seconds for safety
        
        if total_time > 60:
            return f"{total_time // 60} minutes {total_time % 60} seconds"
        else:
            return f"{total_time} seconds"