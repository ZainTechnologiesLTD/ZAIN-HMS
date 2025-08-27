# Enterprise User Management System Documentation

## Overview

This document describes the comprehensive enterprise user management system implemented for the Hospital Management System (HMS). The system provides centralized user creation, role-based permissions, security features, and audit capabilities.

## 🏗️ Architecture Components

### 1. UserManagementService
**Location**: `apps/accounts/services.py`

Centralized service for creating user accounts across all roles with enterprise-grade features:

```python
# Example Usage
user_service = UserManagementService()
user = user_service.create_user_account(
    email='doctor@hospital.com',
    first_name='John',
    last_name='Doe',
    role='DOCTOR',
    hospital=hospital_instance,
    created_by=admin_user,
    additional_data={
        'specialization': 'Cardiology',
        'license_number': 'DOC12345',
        'phone': '+1234567890',
    }
)
```

**Features**:
- ✅ Automatic username generation
- ✅ Secure password generation
- ✅ Role-based permission assignment
- ✅ Email notifications with credentials
- ✅ Audit logging
- ✅ Hospital-based user segregation

### 2. Permission System
**Location**: `apps/accounts/permissions.py`

Role-based access control with mixins for views:

```python
# Example Usage in Views
class DoctorListView(RoleBasedPermissionMixin, HospitalFilterMixin, ListView):
    required_roles = ['admin', 'doctor', 'nurse']
```

**Permission Mixins**:
- `RoleBasedPermissionMixin`: Controls access based on user roles
- `HospitalFilterMixin`: Automatically filters data by user's hospital
- `ModulePermissionMixin`: Controls access to specific modules

### 3. Enhanced User Model
**Location**: `apps/accounts/models.py`

Extended User model with enterprise security features:

**New Security Fields**:
- `must_change_password`: Forces password change on first login
- `last_password_change`: Tracks password change history
- `password_reset_token`: Secure password reset tokens
- `password_reset_at`: Password reset timestamp
- `phone_verified`: Phone verification status
- `email_verified`: Email verification status
- `two_factor_enabled`: 2FA enablement status
- `created_by`: Audit trail of who created the user

## 🔐 Role-Based Permissions

### Role Hierarchy

1. **SUPERADMIN** - Full system access across all hospitals
2. **ADMIN** - Hospital administrator with full access to their hospital
3. **HR_MANAGER** - Can manage staff accounts (doctors, nurses)
4. **DOCTOR** - Patient care, appointments, medical records
5. **NURSE** - Patient care, basic appointments
6. **RECEPTIONIST** - Patient registration, appointments
7. **PHARMACIST** - Pharmacy and medication management
8. **LAB_TECHNICIAN** - Laboratory tests and results
9. **ACCOUNTANT** - Billing and financial reports
10. **PATIENT** - Limited access to own records

### Module Access Matrix

| Role | Patients | Appointments | Billing | Pharmacy | Laboratory | Emergency | Reports |
|------|----------|--------------|---------|----------|------------|-----------|---------|
| ADMIN | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| DOCTOR | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ |
| NURSE | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |
| RECEPTIONIST | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| PHARMACIST | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| PATIENT | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

## 🚀 Implementation in Views

### Updated Module Views

All major modules have been updated to use the enterprise system:

#### Doctors Module (`apps/doctors/views.py`)
```python
class DoctorCreateView(RoleBasedPermissionMixin, CreateView):
    required_roles = ['admin', 'hr_manager']
    
    def form_valid(self, form):
        user = user_service.create_user_account(
            email=doctor.email,
            first_name=doctor.first_name,
            last_name=doctor.last_name,
            role='DOCTOR',
            hospital=self.request.user.hospital,
            created_by=self.request.user,
            additional_data={...}
        )
        doctor.user = user
        doctor.save()
```

#### Patients Module (`apps/patients/views.py`)
```python
class PatientCreateView(RoleBasedPermissionMixin, CreateView):
    required_roles = ['admin', 'receptionist', 'doctor', 'nurse']
    
    def form_valid(self, form):
        # Creates user account for patient if email provided
        if patient.email:
            user = user_service.create_user_account(...)
            patient.user = user
```

#### Nurses Module (`apps/nurses/views.py`)
```python
class NurseCreateView(RoleBasedPermissionMixin, CreateView):
    required_roles = ['admin', 'hr_manager']
```

## 🔒 Security Features

### 1. Password Management
- **Secure Generation**: 12-character passwords with mixed case, numbers, symbols
- **Mandatory Change**: All new users must change password on first login
- **Reset Tokens**: Secure password reset with expiration
- **History Tracking**: Password change timestamps

### 2. Account Security
- **Email Verification**: Optional email verification workflow
- **Phone Verification**: Optional phone verification workflow
- **Two-Factor Authentication**: Ready for 2FA implementation
- **Account Locking**: Extensible for failed login attempts

### 3. Audit & Logging
- **User Creation Logs**: Full audit trail of who created which accounts
- **Permission Changes**: Track role and permission modifications
- **Login Activity**: Ready for session tracking
- **Data Access**: Hospital-based data segregation

## 📧 Email Integration

### Welcome Email System
Automatic email notifications when accounts are created:

```python
# Email contains:
- Temporary username and password
- Link to change password
- Hospital information
- Contact details for support
```

**Current Status**: Ready but requires SMTP configuration in production.

## 🧪 Testing

### Test Suite: `test_enterprise_features.py`

Comprehensive testing of all enterprise features:

```bash
# Run tests
python test_enterprise_features.py
```

**Test Coverage**:
- ✅ User creation for all roles
- ✅ Role-based permissions
- ✅ Username generation
- ✅ Password management
- ✅ Hospital segregation
- ✅ Audit logging

## 🛠️ Configuration

### Settings Required

```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@domain.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'HMS System <noreply@yourhospital.com>'
```

### Environment Variables
```bash
# For production
EMAIL_HOST_USER=your-email@domain.com
EMAIL_HOST_PASSWORD=your-app-password
SECRET_KEY=your-secret-key
DEBUG=False
```

## 📋 Usage Examples

### Creating a Doctor Account
```python
# In DoctorCreateView
user_service = UserManagementService()
user = user_service.create_user_account(
    email='dr.smith@hospital.com',
    first_name='John',
    last_name='Smith',
    role='DOCTOR',
    hospital=request.user.hospital,
    created_by=request.user,
    additional_data={
        'specialization': 'Cardiology',
        'license_number': 'MD123456',
        'phone': '+1234567890',
    }
)
```

### Checking Permissions
```python
# In any view
if not request.user.has_module_permission('patients'):
    return redirect('access_denied')

# Using mixins
class PatientListView(RoleBasedPermissionMixin, ListView):
    required_roles = ['admin', 'doctor', 'nurse']
```

### Hospital Filtering
```python
# Automatic hospital filtering
class DoctorListView(HospitalFilterMixin, ListView):
    def get_queryset(self):
        return self.filter_by_hospital(Doctor.objects.all())
```

## 🔄 Migration Path

### For Existing Users
1. Run migrations to add new User model fields
2. Existing users get `must_change_password=True`
3. Create User accounts for existing Doctors/Nurses/Patients without User links
4. Update all views to use new permission system

### Database Updates
```bash
# Apply migrations
python manage.py makemigrations accounts
python manage.py migrate
```

## 🚀 Future Enhancements

### Phase 2 Features
- [ ] Advanced 2FA with TOTP/SMS
- [ ] Session management and concurrent login limits
- [ ] Advanced audit dashboard
- [ ] Role delegation and temporary permissions
- [ ] API key management for integrations
- [ ] Advanced password policies
- [ ] Bulk user import/export
- [ ] Single Sign-On (SSO) integration

### Monitoring & Analytics
- [ ] User activity dashboards
- [ ] Permission usage analytics
- [ ] Security event monitoring
- [ ] Performance metrics

## 📞 Support

For issues or questions about the enterprise user management system:

1. Check test results: `python test_enterprise_features.py`
2. Review logs in `logs/django.log`
3. Verify permissions in Django admin
4. Test with different user roles

## 🎯 Benefits Achieved

✅ **Centralized Management**: Single service for all user creation
✅ **Security**: Enterprise-grade password and permission management
✅ **Scalability**: Role-based system supports any number of hospitals
✅ **Audit Compliance**: Full tracking of user creation and permissions
✅ **Maintainability**: Clean separation of concerns with mixins
✅ **User Experience**: Automatic account setup with email notifications
✅ **Flexibility**: Easy to extend for new roles and permissions

This enterprise user management system transforms the HMS from a basic application into a production-ready, multi-tenant, secure hospital management platform.
