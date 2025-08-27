"""
Management command to link existing users to staff profiles
Usage: python manage.py link_staff_users
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.staff.models import StaffProfile
from apps.accounts.models import User
from apps.accounts.services import UserManagementService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Link existing users to staff profiles based on email addresses'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=str,
            help='Link specific user by UUID',
        )
        parser.add_argument(
            '--staff-id',
            type=str,
            help='Link specific staff profile by UUID',
        )
        parser.add_argument(
            '--role',
            type=str,
            choices=['NURSE', 'PHARMACIST', 'LAB_TECHNICIAN', 'RADIOLOGIST', 'ACCOUNTANT', 'HR_MANAGER', 'RECEPTIONIST', 'STAFF'],
            help='Only link users with specific role',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be linked without actually making changes',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force linking even if user already has a staff profile',
        )

    def handle(self, *args, **options):
        user_id = options.get('user_id')
        staff_id = options.get('staff_id')
        role_filter = options.get('role')
        dry_run = options.get('dry_run')
        force = options.get('force')

        if user_id and staff_id:
            # Link specific user to specific staff
            self.link_specific_user_staff(user_id, staff_id, dry_run, force)
        elif user_id:
            # Find staff profile for specific user
            self.link_specific_user(user_id, dry_run, force)
        elif staff_id:
            # Find user for specific staff profile
            self.link_specific_staff(staff_id, dry_run, force)
        else:
            # Auto-link based on email addresses
            self.auto_link_users_staff(role_filter, dry_run, force)

    def link_specific_user_staff(self, user_id, staff_id, dry_run, force):
        """Link specific user to specific staff profile"""
        try:
            user = User.objects.get(id=user_id)
            staff = StaffProfile.objects.get(id=staff_id)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User with ID "{user_id}" not found'))
            return
        except StaffProfile.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Staff profile with ID "{staff_id}" not found'))
            return

        # Check if already linked
        if staff.user and not force:
            self.stdout.write(
                self.style.WARNING(f'Staff "{staff.get_full_name()}" is already linked to user "{staff.user.username}". Use --force to override.')
            )
            return

        if hasattr(user, 'staff_profile') and user.staff_profile and not force:
            self.stdout.write(
                self.style.WARNING(f'User "{user.username}" is already linked to staff "{user.staff_profile.get_full_name()}". Use --force to override.')
            )
            return

        if dry_run:
            self.stdout.write(f'Would link user "{user.username}" to staff "{staff.get_full_name()}"')
            return

        try:
            result = UserManagementService.link_user_to_staff(user_id, staff_id)
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully linked user "{user.username}" to staff "{staff.get_full_name()}"')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'Failed to link: {result["message"]}')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error linking user to staff: {str(e)}')
            )

    def link_specific_user(self, user_id, dry_run, force):
        """Find and link staff profile for specific user"""
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User with ID "{user_id}" not found'))
            return

        # Find staff with matching email
        staff_profiles = StaffProfile.objects.filter(
            email__iexact=user.email,
            user__isnull=True
        )

        if not staff_profiles.exists():
            self.stdout.write(
                self.style.WARNING(f'No unlinked staff profile found with email "{user.email}"')
            )
            return

        if staff_profiles.count() > 1:
            self.stdout.write(
                self.style.WARNING(f'Multiple staff profiles found with email "{user.email}":')
            )
            for staff in staff_profiles:
                self.stdout.write(f'  - {staff.get_full_name()} ({staff.position_title}) - ID: {staff.id}')
            self.stdout.write('Use --staff-id to specify which one to link')
            return

        staff = staff_profiles.first()
        
        if dry_run:
            self.stdout.write(f'Would link user "{user.username}" to staff "{staff.get_full_name()}"')
            return

        try:
            result = UserManagementService.link_user_to_staff(user.id, staff.id)
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully linked user "{user.username}" to staff "{staff.get_full_name()}"')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'Failed to link: {result["message"]}')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error linking user to staff: {str(e)}')
            )

    def link_specific_staff(self, staff_id, dry_run, force):
        """Find and link user for specific staff profile"""
        try:
            staff = StaffProfile.objects.get(id=staff_id)
        except StaffProfile.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Staff profile with ID "{staff_id}" not found'))
            return

        # Find user with matching email
        users = User.objects.filter(
            email__iexact=staff.email
        ).exclude(
            staff_profile__isnull=False
        )

        if not users.exists():
            self.stdout.write(
                self.style.WARNING(f'No unlinked user found with email "{staff.email}"')
            )
            return

        if users.count() > 1:
            self.stdout.write(
                self.style.WARNING(f'Multiple users found with email "{staff.email}":')
            )
            for user in users:
                self.stdout.write(f'  - {user.get_full_name()} ({user.username}) - ID: {user.id}')
            self.stdout.write('Use --user-id to specify which one to link')
            return

        user = users.first()
        
        if dry_run:
            self.stdout.write(f'Would link user "{user.username}" to staff "{staff.get_full_name()}"')
            return

        try:
            result = UserManagementService.link_user_to_staff(user.id, staff.id)
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully linked user "{user.username}" to staff "{staff.get_full_name()}"')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'Failed to link: {result["message"]}')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error linking user to staff: {str(e)}')
            )

    def auto_link_users_staff(self, role_filter, dry_run, force):
        """Auto-link users and staff based on email addresses"""
        
        # Get unlinked staff profiles
        staff_query = StaffProfile.objects.filter(user__isnull=True, is_active=True)
        
        # Filter by role if specified
        if role_filter:
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

        unlinked_staff = staff_query.order_by('first_name', 'last_name')
        
        # Find matching users
        potential_links = []
        for staff in unlinked_staff:
            users = User.objects.filter(
                email__iexact=staff.email
            ).exclude(
                staff_profile__isnull=False
            )
            
            if users.count() == 1:
                potential_links.append((users.first(), staff))
            elif users.count() > 1:
                self.stdout.write(
                    self.style.WARNING(f'Multiple users found for staff "{staff.get_full_name()}" ({staff.email})')
                )

        if not potential_links:
            self.stdout.write(
                self.style.SUCCESS('No automatic links possible - all users and staff are already linked or no matching emails found')
            )
            return

        self.stdout.write(f'Found {len(potential_links)} potential automatic links')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No links will be created'))
            for user, staff in potential_links:
                self.stdout.write(f'  Would link: {user.username} -> {staff.get_full_name()} ({staff.position_title})')
            return

        # Confirm action
        confirm = input(f'Link {len(potential_links)} user-staff pairs automatically? [y/N]: ')
        if confirm.lower() != 'y':
            self.stdout.write('Operation cancelled')
            return

        # Create links
        success_count = 0
        error_count = 0

        with transaction.atomic():
            for user, staff in potential_links:
                try:
                    self.stdout.write(f'Linking {user.username} -> {staff.get_full_name()}...', ending='')
                    
                    result = UserManagementService.link_user_to_staff(user.id, staff.id)
                    if result['success']:
                        success_count += 1
                        self.stdout.write(self.style.SUCCESS(' ✓'))
                    else:
                        error_count += 1
                        self.stdout.write(self.style.ERROR(f' ✗ {result["message"]}'))
                        
                except Exception as e:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(f' ✗ Error: {str(e)}'))
                    logger.error(f'Failed to link user {user.id} to staff {staff.id}: {str(e)}')

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Successfully linked {success_count} user-staff pairs'))
        if error_count > 0:
            self.stdout.write(self.style.WARNING(f'{error_count} errors occurred'))
