from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string


User = get_user_model()


class UserManagementService:
    @staticmethod
    def create_user_account(email, first_name, last_name, role, tenant_code=None, created_by=None, additional_data=None):
        """
        Create a new user account with a temporary password.

        Args:
            email (str): Email address (used as username).
            first_name (str)
            last_name (str)
            role (str): One of CustomUser.ROLE_CHOICES
            tenant_code (str|None): Hospital/tenant code for context; not persisted on user model.
            created_by: Ignored (no field on user); kept for API compatibility.
            additional_data (dict|None): Extra attrs to set on the user if present.

        Returns:
            User: The created user instance.
        """
        if not email:
            raise ValueError("Email is required to create a user account.")

        if User.objects.filter(email=email).exists():
            raise ValueError(f"A user with the email {email} already exists.")

        password = get_random_string(12)

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name or "",
            last_name=last_name or "",
            role=role,
            is_active=True,
        )

        if additional_data:
            for key, value in additional_data.items():
                if hasattr(user, key):
                    setattr(user, key, value)
        user.save()

        # TODO: send onboarding email with password reset link.
        print(f"Created user {email} with temporary password: {password}")

        return user
