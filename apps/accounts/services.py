from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from django.core.exceptions import ValidationError
import logging


User = get_user_model()
logger = logging.getLogger(__name__)

class UserManagementService:
    """Simplified user management service for ZAIN HMS unified system"""
    
    @staticmethod
    def create_user_account(email, first_name, last_name, role, username=None, password=None, created_by=None, additional_data=None):
        """
        Create a new user account in ZAIN HMS unified system.
        
        Args:
            email (str): User's email address (must be unique)
            first_name (str): User's first name
            last_name (str): User's last name  
            role (str): User role from ROLE_CHOICES
            username (str|None): Optional username. If None, generated from email
            password (str|None): Optional password. If None, auto-generated
            created_by (User|None): User who is creating this account
            additional_data (dict|None): Extra user fields like phone, etc.
            
        Returns:
            tuple: (user_instance, raw_password, success_message)
            
        Raises:
            ValidationError: If email exists or validation fails
        """
        try:
            # Validate email uniqueness
            if User.objects.filter(email=email).exists():
                logger.warning(f"Account creation failed: Email {email} already exists")
                raise ValidationError(f"User with email '{email}' already exists in ZAIN HMS")
            
            # Generate username if not provided
            if not username:
                username = email.split('@')[0]
                # Ensure username uniqueness
                counter = 1
                original_username = username
                while User.objects.filter(username=username).exists():
                    username = f"{original_username}{counter}"
                    counter += 1
            else:
                # Check username uniqueness
                if User.objects.filter(username=username).exists():
                    raise ValidationError(f"Username '{username}' already exists in ZAIN HMS")
            
            # Generate password if not provided
            raw_password = password or get_random_string(12)
            
            # Create user instance
            user_data = {
                'email': email,
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
                'role': role,
                'is_active': True,
            }
            
            # Add additional data if provided
            if additional_data and isinstance(additional_data, dict):
                user_data.update(additional_data)
            
            # Create user
            user = User.objects.create_user(
                password=raw_password,
                **user_data
            )
            
            success_message = f"User account created successfully for {first_name} {last_name} in ZAIN HMS"
            logger.info(f"User account created: {user.username} ({user.email}) with role {role}")
            
            return user, raw_password, success_message
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating user account: {e}")
            raise ValidationError(f"Failed to create user account: {str(e)}")
    
    @staticmethod
    def update_user_account(user, **kwargs):
        """Update user account details"""
        try:
            for field, value in kwargs.items():
                if hasattr(user, field):
                    setattr(user, field, value)
            user.save()
            logger.info(f"User account updated: {user.username}")
            return user
        except Exception as e:
            logger.error(f"Error updating user account {user.username}: {e}")
            raise ValidationError(f"Failed to update user account: {str(e)}")
    
    @staticmethod
    def deactivate_user(user, deactivated_by=None):
        """Deactivate a user account"""
        try:
            user.is_active = False
            user.save(update_fields=['is_active'])
            logger.info(f"User account deactivated: {user.username} by {deactivated_by}")
            return True
        except Exception as e:
            logger.error(f"Error deactivating user {user.username}: {e}")
            return False
    
    @staticmethod
    def activate_user(user, activated_by=None):
        """Activate a user account"""
        try:
            user.is_active = True
            user.save(update_fields=['is_active'])
            logger.info(f"User account activated: {user.username} by {activated_by}")
            return True
        except Exception as e:
            logger.error(f"Error activating user {user.username}: {e}")
            return False
