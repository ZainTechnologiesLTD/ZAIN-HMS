# Zain HMS - Multi-Tenant SaaS Architecture

## Overview

Zain HMS has been transformed into a comprehensive **Software as a Service (SaaS)** Hospital Management System with **multi-tenant architecture**. This means:

- **Super Admins** can create and manage multiple hospitals
- Each **Hospital** operates as an independent tenant with its own database
- **Complete data isolation** between hospitals
- **Scalable architecture** supporting unlimited hospitals
- **Centralized management** with hospital-specific customization

## Architecture Components

### 1. Multi-Tenant Database Strategy

The system uses a **"Database per Tenant"** approach for maximum isolation:

```
Default Database (Main)
├── Hospital Management (accounts.Hospital)
├── User Authentication (accounts.User)
├── Department Management (accounts.Department)
└── System Administration

Hospital-Specific Databases
├── hospital_DEMO001/
│   ├── Patients
│   ├── Appointments
│   ├── Billing
│   ├── Laboratory
│   └── All other hospital data
├── hospital_ABC123/
└── hospital_XYZ789/
```

### 2. Database Router (`apps/core/db_router.py`)

The `MultiTenantDBRouter` automatically routes database queries:

- **Shared Apps** (accounts, core) → Default database
- **Tenant Apps** (patients, appointments, billing, etc.) → Hospital-specific database
- **Automatic routing** based on hospital context
- **Thread-safe** hospital context management

### 3. Middleware Stack

```python
MIDDLEWARE = [
    # Standard Django middleware
    'apps.core.middleware.HospitalMiddleware',
    'apps.core.db_router.TenantMiddleware',  # New tenant middleware
    'apps.core.middleware.ActivityLogMiddleware',
    # Other middleware
]
```

## User Roles & Permissions

### Super Administrator (SUPERADMIN)
- Create and manage hospitals
- Access all hospital data
- Manage subscriptions and billing
- System-wide administration
- Access to Django admin panel

### Hospital Administrator (ADMIN)
- Manage their hospital settings
- Create and manage hospital users
- Access all hospital modules
- Hospital-specific administration
- Cannot access other hospitals

### Hospital Staff (Various Roles)
- DOCTOR, NURSE, RECEPTIONIST, etc.
- Access based on role permissions
- Limited to their assigned hospital
- Module-specific access control

## Getting Started

### 1. Initial Setup

Run the comprehensive setup script:

```bash
python setup_saas.py
```

This will:
- Setup the main database
- Create a super administrator
- Optionally create a demo hospital
- Configure the multi-tenant environment

### 2. Manual Setup (Alternative)

#### Create Super Admin:
```bash
python manage.py create_superadmin \
    --username superadmin \
    --email admin@yourdomain.com \
    --password your_secure_password \
    --first-name Super \
    --last-name Admin
```

#### Create Hospital:
```bash
python manage.py setup_hospital \
    --name "City General Hospital" \
    --code "CGH001" \
    --email "admin@citygeneral.com" \
    --phone "+1234567890" \
    --address "123 Medical Center Drive" \
    --city "Metropolis" \
    --state "NY" \
    --country "USA" \
    --plan "PROFESSIONAL" \
    --admin-username "cgh_admin" \
    --admin-email "admin@citygeneral.com" \
    --admin-password "secure_password" \
    --admin-first-name "Hospital" \
    --admin-last-name "Administrator"
```

### 3. Access Points

- **Super Admin Dashboard**: `/auth/superadmin/`
- **Django Admin Panel**: `/admin/`
- **Hospital Login**: `/auth/login/`
- **Hospital Settings**: `/auth/hospital/settings/`

## Database Management

### Automatic Database Creation

When a hospital is created:
1. Hospital record is saved to the main database
2. New database is automatically created (e.g., `hospital_CGH001`)
3. All tenant app migrations are run on the new database
4. Hospital admin user is created and linked

### Manual Database Operations

#### Create Database for Existing Hospital:
```python
from apps.core.db_router import TenantDatabaseManager
TenantDatabaseManager.create_hospital_database('HOSPITAL_CODE')
```

#### Set Hospital Context:
```python
TenantDatabaseManager.set_hospital_context('HOSPITAL_CODE')
# Now all tenant app queries will use hospital_HOSPITAL_CODE database
```

#### Database Configuration:

**Development (SQLite):**
```python
# Each hospital gets its own SQLite file
hospital_ABC123 = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': BASE_DIR / 'hospitals/ABC123/db.sqlite3',
}
```

**Production (PostgreSQL):**
```python
# Each hospital gets its own PostgreSQL database
hospital_ABC123 = {
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': 'zain_hms_ABC123',
    'USER': 'postgres',
    'PASSWORD': 'password',
    'HOST': 'localhost',
    'PORT': '5432',
}
```

## Hospital Management

### Super Admin Features

1. **Hospital Creation & Management**
   - Create new hospitals with automatic database setup
   - Manage subscriptions and billing
   - View hospital statistics and analytics
   - Monitor system health and performance

2. **User Management**
   - Create hospital administrators
   - Manage system-wide user permissions
   - Monitor user activities across hospitals

3. **System Administration**
   - Database backup and recovery
   - System configuration and updates
   - Performance monitoring and optimization

### Hospital Admin Features

1. **Hospital Customization**
   - Upload hospital logo and branding
   - Configure timezone, currency, language
   - Set business rules and preferences
   - Manage contact information

2. **User Management**
   - Create and manage hospital staff
   - Set role-based permissions
   - Monitor user activities within hospital

3. **Module Configuration**
   - Enable/disable specific modules
   - Configure module-specific settings
   - Customize workflows and processes

## Security & Data Isolation

### Data Isolation Mechanisms

1. **Database Level**: Each hospital has its own database
2. **Application Level**: Middleware enforces hospital context
3. **User Level**: Role-based access control
4. **API Level**: Hospital-specific API endpoints

### Security Features

1. **Authentication & Authorization**
   - Multi-factor authentication support
   - Session management and tracking
   - Password policies and validation

2. **Data Protection**
   - Encrypted data transmission
   - Secure file storage
   - Audit logging and monitoring

3. **Compliance**
   - HIPAA compliance features
   - Data retention policies
   - Privacy controls and user consent

## Subscription Management

### Subscription Plans

1. **TRIAL** (30 days)
   - Limited features
   - Basic support
   - Up to 100 patients

2. **BASIC** (Monthly/Yearly)
   - Core HMS features
   - Email support
   - Up to 1,000 patients

3. **PROFESSIONAL** (Monthly/Yearly)
   - Advanced features
   - Priority support
   - Up to 10,000 patients
   - Custom reporting

4. **ENTERPRISE** (Custom)
   - All features
   - Dedicated support
   - Unlimited patients
   - Custom integrations

### Billing Integration

```python
# Example subscription management
hospital.subscription_plan = 'PROFESSIONAL'
hospital.subscription_status = 'ACTIVE'
hospital.subscription_end = date.today() + timedelta(days=365)
hospital.save()
```

## Development Guidelines

### Adding New Tenant Apps

1. Add app to `TENANT_APPS` in `db_router.py`
2. Ensure all models have `hospital` foreign key
3. Use hospital context in views and APIs
4. Test with multiple hospitals

### Database Queries

```python
# Always ensure hospital context
from apps.core.db_router import TenantDatabaseManager

# Set context
TenantDatabaseManager.set_hospital_context(hospital.code)

# Query tenant data
patients = Patient.objects.all()  # Automatically uses hospital DB

# Clear context when done
TenantDatabaseManager.set_hospital_context(None)
```

### API Development

```python
# Example API view with hospital context
class PatientViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        # Hospital context is set by middleware
        return Patient.objects.all()
    
    def perform_create(self, serializer):
        # Automatically associate with current hospital
        serializer.save(hospital=self.request.user.hospital)
```

## Deployment Considerations

### Production Deployment

1. **Database Configuration**
   - Use PostgreSQL for production
   - Configure connection pooling
   - Set up automated backups

2. **Infrastructure**
   - Load balancer configuration
   - CDN for static files
   - Redis for caching and sessions

3. **Monitoring**
   - Database performance monitoring
   - Application performance monitoring
   - Log aggregation and analysis

### Scaling Strategies

1. **Horizontal Scaling**
   - Database sharding by hospital
   - Microservices architecture
   - Container orchestration

2. **Performance Optimization**
   - Database indexing strategies
   - Query optimization
   - Caching implementation

## Troubleshooting

### Common Issues

1. **Database Routing Problems**
   ```bash
   # Check hospital context
   from apps.core.db_router import TenantDatabaseManager
   print(TenantDatabaseManager._get_current_hospital_db())
   ```

2. **Missing Hospital Database**
   ```bash
   # Create missing database
   python manage.py shell
   >>> from apps.core.db_router import TenantDatabaseManager
   >>> TenantDatabaseManager.create_hospital_database('HOSPITAL_CODE')
   ```

3. **Migration Issues**
   ```bash
   # Migrate specific hospital database
   python manage.py migrate --database=hospital_CODE123
   ```

### Debugging Tools

1. **Database Router Logging**
   - Enable DEBUG logging for database queries
   - Monitor database routing decisions

2. **Hospital Context Debugging**
   - Check middleware processing
   - Verify user hospital assignments

## Support & Documentation

### Additional Resources

- **Management Commands**: Use `--help` flag for detailed options
- **Admin Interface**: Comprehensive hospital management tools
- **API Documentation**: Auto-generated API docs at `/api/docs/`
- **Monitoring Dashboard**: Real-time system monitoring

### Getting Help

1. Check the logs in `logs/` directory
2. Use Django admin for database inspection
3. Review middleware and router configurations
4. Contact system administrator for production issues

---

This multi-tenant SaaS architecture provides a robust foundation for scaling the Hospital Management System to serve multiple hospitals while maintaining complete data isolation and security.
