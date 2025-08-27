"""
Management command to create user accounts for doctors who don't have them
Usage: python manage.py create_doctor_users
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.doctors.models import Doctor
from apps.accounts.models import User, Hospital
from apps.accounts.services import UserManagementService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Create user accounts for doctors who do not have them'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hospital-id',
            type=str,
            help='Only create users for doctors in the specified hospital (UUID)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually creating users',
        )
        parser.add_argument(
            '--created-by',
            type=str,
            help='Username of the user who should be marked as creator (defaults to superadmin)',
        )

    def handle(self, *args, **options):
        hospital_id = options.get('hospital_id')
        dry_run = options.get('dry_run')
        created_by_username = options.get('created_by')
        
        # Get the user who will be marked as creator
        created_by_user = None
        if created_by_username:
            try:
                created_by_user = User.objects.get(username=created_by_username)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User "{created_by_username}" not found')
                )
                return
        else:
            # Default to first superuser
            created_by_user = User.objects.filter(is_superuser=True).first()
            if not created_by_user:
                self.stdout.write(
                    self.style.ERROR('No superuser found. Please create a superuser first or specify --created-by')
                )
                return

        # Get doctors without user accounts
        doctors_query = Doctor.objects.filter(user__isnull=True, is_active=True)
        
        if hospital_id:
            try:
                hospital = Hospital.objects.get(id=hospital_id)
                # Filter by hospital if the doctor model has a hospital relationship
                # This depends on your actual model structure
                doctors_query = doctors_query.filter(hospital=hospital)
                self.stdout.write(f'Filtering by hospital: {hospital.name}')
            except Hospital.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Hospital with ID "{hospital_id}" not found')
                )
                return

        doctors_without_users = doctors_query.order_by('first_name', 'last_name')
        total_doctors = doctors_without_users.count()

        if total_doctors == 0:
            self.stdout.write(
                self.style.SUCCESS('All active doctors already have user accounts!')
            )
            return

        self.stdout.write(f'Found {total_doctors} doctors without user accounts')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No users will be created'))
            self.stdout.write('Doctors that would get user accounts:')
            for doctor in doctors_without_users:
                self.stdout.write(f'  - Dr. {doctor.get_full_name()} ({doctor.email})')
            return

        # Confirm action
        if not options.get('verbosity', 1) == 0:
            confirm = input(f'Create user accounts for {total_doctors} doctors? [y/N]: ')
            if confirm.lower() != 'y':
                self.stdout.write('Operation cancelled')
                return

        # Create user accounts
        success_count = 0
        error_count = 0
        
        with transaction.atomic():
            for doctor in doctors_without_users:
                try:
                    self.stdout.write(f'Creating user for Dr. {doctor.get_full_name()}...', ending='')
                    
                    # Determine hospital (you may need to adjust this based on your model)
                    hospital = created_by_user.hospital  # Fallback to creator's hospital
                    
                    user = UserManagementService.create_user_for_existing_doctor(
                        doctor_id=doctor.id,
                        created_by_user=created_by_user
                    )
                    
                    success_count += 1
                    self.stdout.write(self.style.SUCCESS(' ✓'))
                    
                except Exception as e:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(f' ✗ Error: {str(e)}'))
                    logger.error(f'Failed to create user for doctor {doctor.id}: {str(e)}')

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Successfully created {success_count} user accounts'))
        if error_count > 0:
            self.stdout.write(self.style.WARNING(f'{error_count} errors occurred'))
        
        self.stdout.write('')
        self.stdout.write('User accounts have been created with temporary passwords.')
        self.stdout.write('Login credentials have been sent to the doctors\' email addresses.')
        self.stdout.write('Doctors must change their passwords on first login.')
