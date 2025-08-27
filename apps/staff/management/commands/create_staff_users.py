"""
Management command to create user accounts for staff who don't have them
Usage: python manage.py create_staff_users
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.staff.models import StaffProfile
from apps.accounts.models import User, Hospital
from apps.accounts.services import UserManagementService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Create user accounts for staff members who do not have them'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hospital-id',
            type=str,
            help='Only create users for staff in the specified hospital (UUID)',
        )
        parser.add_argument(
            '--role',
            type=str,
            choices=['NURSE', 'PHARMACIST', 'LAB_TECHNICIAN', 'RADIOLOGIST', 'ACCOUNTANT', 'HR_MANAGER', 'RECEPTIONIST', 'STAFF'],
            help='Only create users for staff with specific role/position',
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
        role_filter = options.get('role')
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

        # Get staff without user accounts
        staff_query = StaffProfile.objects.filter(user__isnull=True, is_active=True)
        
        if hospital_id:
            try:
                hospital = Hospital.objects.get(id=hospital_id)
                staff_query = staff_query.filter(hospital=hospital)
                self.stdout.write(f'Filtering by hospital: {hospital.name}')
            except Hospital.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Hospital with ID "{hospital_id}" not found')
                )
                return
        
        # Filter by role if specified
        if role_filter:
            # Filter by position title or look for role-specific keywords
            role_keywords = {
                'NURSE': ['nurse', 'nursing'],
                'PHARMACIST': ['pharmacist', 'pharmacy'],
                'LAB_TECHNICIAN': ['lab technician', 'laboratory technician', 'lab tech'],
                'RADIOLOGIST': ['radiologist', 'radiology'],
                'ACCOUNTANT': ['accountant', 'accounting', 'finance'],
                'HR_MANAGER': ['hr manager', 'human resources', 'hr'],
                'RECEPTIONIST': ['receptionist', 'reception', 'front desk'],
                'STAFF': ['staff', 'assistant'],
            }
            
            keywords = role_keywords.get(role_filter, [])
            if keywords:
                from django.db.models import Q
                query = Q()
                for keyword in keywords:
                    query |= Q(position_title__icontains=keyword)
                staff_query = staff_query.filter(query)
            
            self.stdout.write(f'Filtering by role: {role_filter}')

        staff_without_users = staff_query.order_by('first_name', 'last_name')
        total_staff = staff_without_users.count()

        if total_staff == 0:
            filter_msg = ""
            if hospital_id or role_filter:
                filter_msg = " matching the specified criteria"
            self.stdout.write(
                self.style.SUCCESS(f'All active staff{filter_msg} already have user accounts!')
            )
            return

        self.stdout.write(f'Found {total_staff} staff members without user accounts')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No users will be created'))
            self.stdout.write('Staff that would get user accounts:')
            for staff in staff_without_users:
                determined_role = UserManagementService._determine_role_from_position(staff.position_title)
                self.stdout.write(f'  - {staff.get_full_name()} ({staff.position_title}) -> {determined_role} ({staff.email})')
            return

        # Confirm action
        if not options.get('verbosity', 1) == 0:
            confirm = input(f'Create user accounts for {total_staff} staff members? [y/N]: ')
            if confirm.lower() != 'y':
                self.stdout.write('Operation cancelled')
                return

        # Create user accounts
        success_count = 0
        error_count = 0
        
        with transaction.atomic():
            for staff in staff_without_users:
                try:
                    # Determine role from position title
                    determined_role = UserManagementService._determine_role_from_position(staff.position_title)
                    
                    self.stdout.write(f'Creating user for {staff.get_full_name()} ({staff.position_title}) as {determined_role}...', ending='')
                    
                    user = UserManagementService.create_user_for_existing_staff(
                        staff_profile_id=staff.id,
                        created_by_user=created_by_user
                    )
                    
                    success_count += 1
                    self.stdout.write(self.style.SUCCESS(' ✓'))
                    
                except Exception as e:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(f' ✗ Error: {str(e)}'))
                    logger.error(f'Failed to create user for staff {staff.id}: {str(e)}')

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Successfully created {success_count} user accounts'))
        if error_count > 0:
            self.stdout.write(self.style.WARNING(f'{error_count} errors occurred'))
        
        self.stdout.write('')
        self.stdout.write('User accounts have been created with temporary passwords.')
        self.stdout.write('Login credentials have been sent to the staff members\' email addresses.')
        self.stdout.write('Staff members must change their passwords on first login.')
        
        # Show role distribution
        if success_count > 0:
            self.stdout.write('')
            self.stdout.write('Created users by role:')
            created_staff = StaffProfile.objects.filter(user__isnull=False, user__created_by=created_by_user).select_related('user')
            role_counts = {}
            for staff in created_staff:
                role = staff.user.get_role_display()
                role_counts[role] = role_counts.get(role, 0) + 1
            
            for role, count in role_counts.items():
                self.stdout.write(f'  - {role}: {count}')
