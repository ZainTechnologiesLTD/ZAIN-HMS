# 🏥 Automatic Hospital Database Migration Guide

## 🎯 Overview

When you create a new hospital through the Django admin interface, the system will automatically:

1. **Create a dedicated database** for the hospital with complete data isolation
2. **Migrate all necessary modules** to make the hospital fully functional
3. **Configure database routing** for seamless multi-tenant operation  
4. **Set up admin permissions** for the hospital administrator
5. **Display a success message** with direct access links

## 🚀 How It Works

### Automatic Creation (Recommended)

1. **Access Django Admin**: Go to `http://127.0.0.1:8000/admin/`
2. **Navigate to Hospital Management**: Click on "Hospital Tenants" → "Tenants" 
3. **Add New Hospital**: Click "Add Tenant"
4. **Fill Required Fields**:
   - **Hospital Name**: Display name (e.g., "City General Hospital")
   - **Subdomain**: Unique identifier (e.g., "city-general") - will create `hospital_city-general` database
   - **Administrator**: Select or create a user with Hospital Admin role
   - **Contact Information**: Address, phone, email, website
   - **Subscription Settings**: Plan, dates, enabled modules

5. **Save Hospital**: Click "Save" 
   
6. **Automatic Magic Happens**:
   ```
   ✅ Creates SQLite database: hospital_[subdomain]
   ✅ Migrates core Django apps (contenttypes, auth)
   ✅ Migrates all hospital modules:
      • Patient Management        • Appointments
      • Doctor Management        • Nurse Management  
      • Billing & Invoicing      • Laboratory
      • Emergency Care           • Inventory
      • Analytics & Reports      • Human Resources
      • Surgery Management       • Telemedicine
      • Room Management          • OPD/IPD Management
      • Notifications            • Contact Management
      • Feedback System          • Dashboard
   ```

7. **Success Confirmation**: You'll see a detailed success message with:
   - Hospital name and database created
   - List of all migrated modules
   - Direct link to hospital dashboard

### Database Management Actions

From the hospital list page, you can perform these actions on selected hospitals:

#### 🏗️ Create Database
- Creates database for hospitals that don't have one
- Migrates all necessary modules
- Safe to use on existing hospitals (won't overwrite)

#### 🔍 Verify Database  
- Checks if database exists and is accessible
- Shows table count and connection status
- Useful for troubleshooting

#### 🔄 Recreate Database
- **⚠️ DANGER**: Completely deletes and recreates database
- **Permanently destroys all hospital data**
- Only use as last resort for corrupted databases
- Requires superuser permissions

## 📊 Database Status Indicators

In the hospital list, you'll see database status icons:

- **✅ Ready**: Database exists with all tables (10+ tables)
- **⚠️ Incomplete**: Database exists but may be missing tables
- **❌ Missing/Error**: Database doesn't exist or connection failed
- **❓ Unknown**: Unable to determine status

## 🛠️ Manual Management

### Command Line Creation
Create a test hospital with full database setup:

```bash
# Create test hospital with database
python manage.py create_test_hospital \
    --name "Test Hospital" \
    --subdomain "test-hospital" \
    --admin-username "hospital_admin" \
    --admin-email "admin@testhospital.com" \
    --admin-password "secure_password"

# Create hospital without database (for testing admin interface)
python manage.py create_test_hospital --skip-database
```

### Direct Database Creation
```python
from apps.core.db_router import TenantDatabaseManager

# Create database for existing hospital
TenantDatabaseManager.create_hospital_database('hospital_code')

# Verify database exists
# Check Django admin for status indicators
```

## 🏗️ What Gets Migrated

### Core Django Apps
- `contenttypes`: Content type framework
- `auth`: Authentication and permissions

### Hospital Management Modules
- **Patient Management**: Patient records, registration, medical history
- **Appointment System**: Scheduling, calendar management, notifications
- **Staff Management**: Doctors, nurses, administrative staff profiles
- **Medical Modules**: Laboratory tests, radiology, surgery, emergency care
- **Business Modules**: Billing, invoicing, inventory management, analytics
- **Communication**: Notifications, telemedicine, feedback systems
- **Administration**: Room management, IPD/OPD, HR, dashboard

### Database Structure
```
hospital_[subdomain]/
├── Core Tables (auth, contenttypes)
├── Patient Tables (patients_patient, patients_medicalhistory, etc.)
├── Appointment Tables (appointments_appointment, appointments_schedule, etc.)  
├── Staff Tables (doctors_doctor, nurses_nurse, staff_staff, etc.)
├── Medical Tables (laboratory_*, radiology_*, surgery_*, etc.)
├── Business Tables (billing_*, inventory_*, analytics_*, etc.)
└── Communication Tables (notifications_*, telemedicine_*, etc.)
```

## 🎯 Access Patterns

### Hospital-Specific Access
Each hospital gets its own URL pattern:
```
http://[subdomain].localhost:8000/
```

Examples:
- `http://city-general.localhost:8000/` → City General Hospital
- `http://test-hospital.localhost:8000/` → Test Hospital  
- `http://memorial-care.localhost:8000/` → Memorial Care Hospital

### Module URLs
Within each hospital:
```
http://[subdomain].localhost:8000/patients/     → Patient Management
http://[subdomain].localhost:8000/appointments/ → Appointments
http://[subdomain].localhost:8000/laboratory/   → Laboratory
http://[subdomain].localhost:8000/billing/      → Billing
```

## 🔧 Troubleshooting

### Hospital Database Not Created
1. Check server logs for error messages
2. Verify subdomain is unique and valid
3. Ensure database directory has write permissions
4. Use "Create Database" action from hospital list
5. Check Django admin database status indicators

### Missing Tables in Database  
1. Use "Verify Database" action to check table count
2. If incomplete, use "Create Database" action to add missing tables
3. For persistent issues, consider "Recreate Database" (⚠️ destroys data)

### Permission Errors
1. Ensure hospital admin user has correct role
2. Check TenantAccess records are created
3. Verify user is assigned to correct hospital

### Database Connection Issues
1. Check that hospital databases are in Django settings
2. Restart Django server to reload database configurations
3. Verify database files exist in `hospitals/` directory

## 📈 Benefits

### Complete Data Isolation
- Each hospital has its own database
- No data mixing between hospitals
- Enhanced security and privacy

### Automatic Setup
- No manual database configuration
- All modules ready immediately
- Consistent database structure

### Easy Management
- Visual status indicators
- Bulk operations support
- Comprehensive error reporting

### Scalable Architecture  
- Add unlimited hospitals
- Independent database management
- Multi-tenant ready

## 🎉 Success Metrics

After creating a hospital, you should see:

- ✅ **Hospital Record Created**: Hospital appears in admin list
- ✅ **Database Created**: Database status shows "✅ Ready" 
- ✅ **Modules Available**: All 15+ modules migrated successfully
- ✅ **Admin Access**: Hospital admin can log in and access dashboard
- ✅ **Routing Works**: Hospital URL loads correctly
- ✅ **Data Isolation**: Hospital has its own isolated database

## 💡 Pro Tips

1. **Use descriptive subdomains**: They become part of URLs and database names
2. **Create admin users first**: Easier to assign during hospital creation
3. **Test with test hospitals**: Use `create_test_hospital` command for testing
4. **Monitor database status**: Check status indicators regularly
5. **Backup before recreating**: "Recreate Database" destroys all data
6. **Use actions for bulk operations**: Select multiple hospitals for batch operations

---

**🏥 Your Hospital Management System now supports automatic database migration with visual feedback and comprehensive management tools!**
