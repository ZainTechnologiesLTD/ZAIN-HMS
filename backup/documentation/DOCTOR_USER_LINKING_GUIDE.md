# Doctor-User Account Linking System

## Overview

This system provides a comprehensive solution for linking user accounts with existing doctor records in the ZAIN Hospital Management System. It addresses the scenario where you have doctor records but need to create user accounts for them to access the system.

## How It Works

### Current Implementation

1. **Automatic Linking**: When creating a new doctor, a user account is automatically created and linked
2. **Existing Doctor Support**: For doctors already in the system, you can:
   - Create a new user account for them
   - Link them to an existing user account
   - Manage the relationship between doctors and users

### Key Components

#### 1. Models
- **Doctor Model**: Has a `OneToOneField` to the User model (`user` field)
- **User Model**: Extended with doctor-specific information and roles

#### 2. Services
- **UserManagementService**: Centralized service for user account creation and management
  - `create_user_for_existing_doctor()`: Creates a user account for an existing doctor
  - `link_user_to_doctor()`: Links an existing user to an existing doctor
  - `create_user_account()`: General user creation with role-based permissions

#### 3. Views
- **CreateUserForDoctorView**: Creates user account for existing doctor
- **LinkDoctorUserView**: Interface to link existing user to existing doctor
- **DoctorsWithoutUsersView**: Lists all doctors without user accounts
- **Doctor Detail/List Views**: Enhanced with user account status

#### 4. Templates
- Enhanced doctor list showing user account status
- Doctor detail view with user management section
- Dedicated linking interface
- Management views for bulk operations

## Usage Scenarios

### Scenario 1: Create User for Existing Doctor

**When to use**: You have a doctor record but they don't have a login account

**How to do it**:
1. Go to the doctor's detail page
2. Click "Create User Account" in the User Account Management section
3. System automatically creates account using doctor's information
4. Email with login credentials is sent to the doctor

**Programmatically**:
```python
from apps.accounts.services import UserManagementService

user = UserManagementService.create_user_for_existing_doctor(
    doctor_id=doctor.id,
    created_by_user=request.user
)
```

### Scenario 2: Link Existing User to Existing Doctor

**When to use**: You have both a doctor record and a separate user account that should be linked

**How to do it**:
1. Go to the doctor's detail page
2. Click "Link Existing User"
3. Select from available DOCTOR role users
4. Confirm the linking

**Programmatically**:
```python
from apps.accounts.services import UserManagementService

UserManagementService.link_user_to_doctor(
    user_id=user.id,
    doctor_id=doctor.id,
    linked_by_user=request.user
)
```

### Scenario 3: Bulk Create Users for Multiple Doctors

**When to use**: You have many doctors without user accounts

**How to do it**:
1. Use the management command:
```bash
python manage.py create_doctor_users
```

**Options**:
```bash
# Dry run (see what would happen)
python manage.py create_doctor_users --dry-run

# Filter by hospital
python manage.py create_doctor_users --hospital-id <hospital-uuid>

# Specify creator
python manage.py create_doctor_users --created-by admin_username
```

### Scenario 4: Find Doctors Without User Accounts

**How to do it**:
1. Go to Doctors → "Doctors Without Accounts" button
2. Bulk create accounts or manage individually

## Web Interface

### Doctor List View
- Shows user account status for each doctor
- Quick "Create" link for doctors without accounts
- Badge showing "Linked" or "No Account" status

### Doctor Detail View
- User Account Management section (admin only)
- Shows linked user information if exists
- Buttons to create, link, or unlink user accounts

### Dedicated Management Views
- **Doctors Without Users**: Lists all doctors needing user accounts
- **Link User Interface**: Clean interface for linking existing users

## Security & Permissions

### Role-Based Access
- Only `ADMIN` and `SUPERADMIN` roles can manage user-doctor relationships
- Regular users cannot see user management sections

### Validation
- Prevents linking one doctor to multiple users
- Prevents linking one user to multiple doctors
- Email uniqueness validation
- License number uniqueness validation

## Email Notifications

When a user account is created for a doctor:
- Welcome email sent with temporary credentials
- Instructions for first login and password change
- Contact information for support

## API Endpoints

### Available URLs
```python
# Create user for existing doctor (POST)
/doctors/<id>/create-user/

# Link existing user to doctor (GET/POST)
/doctors/<id>/link-user/

# Unlink user from doctor (POST - AJAX)
/doctors/<id>/unlink-user/

# List doctors without users
/doctors/without-users/
```

## Database Relationships

```
Doctor Model:
- user = OneToOneField(User, null=True, blank=True)

User Model:
- role = 'DOCTOR' for doctor users
- hospital = ForeignKey(Hospital)
```

## Error Handling

### Common Errors and Solutions

1. **"Doctor already has a user account"**
   - Solution: Check if doctor.user exists before creating

2. **"User already linked to another doctor"**
   - Solution: Verify user isn't already associated with another doctor

3. **"Email already exists"**
   - Solution: Check for existing users with the same email

## Best Practices

### For Administrators
1. **Regular Audits**: Periodically check for doctors without user accounts
2. **Bulk Operations**: Use management command for bulk user creation
3. **Email Verification**: Ensure doctor email addresses are correct before creating accounts
4. **Documentation**: Keep records of when user accounts are created

### For Developers
1. **Transaction Safety**: Use database transactions for linking operations
2. **Logging**: All user creation/linking operations are logged
3. **Error Handling**: Always handle exceptions gracefully
4. **Testing**: Test both individual and bulk operations

## Troubleshooting

### Common Issues

1. **Emails not sending**
   - Check Django email configuration
   - Verify SMTP settings
   - Check spam folders

2. **Permission denied errors**
   - Verify user role is ADMIN or SUPERADMIN
   - Check hospital relationships

3. **Duplicate user creation**
   - Always check if doctor.user exists before creating
   - Use the provided service methods for safety

### Debug Commands

```bash
# Check doctors without users
python manage.py shell
>>> from apps.doctors.models import Doctor
>>> Doctor.objects.filter(user__isnull=True).count()

# Check users without doctors
>>> from apps.accounts.models import User
>>> User.objects.filter(role='DOCTOR', doctor__isnull=True).count()
```

## Future Enhancements

Potential improvements to consider:
1. **Bulk linking interface** for existing users
2. **Import/export functionality** for user management
3. **Automated user creation** based on specific triggers
4. **Enhanced email templates** with hospital branding
5. **Two-factor authentication** setup during user creation

This system provides a robust foundation for managing doctor-user relationships while maintaining data integrity and security.
