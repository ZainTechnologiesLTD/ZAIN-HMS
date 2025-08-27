# Enhanced Multi-Hospital User Management System

## 🎯 Problem Solved

Your question highlighted important real-world scenarios:

1. **Different user types should have different login experiences**
2. **Doctors/nurses working at multiple hospitals need flexible access**
3. **Single email/phone for users working at multiple locations**

## 🔧 Complete Solution Implementation

### 1. **User Login Flow by Role**

#### **SUPERADMIN Users**
```
Login → No hospital in session → Redirect to Hospital Selection → Choose hospital → Dashboard
```
- Can access ALL hospitals in the system
- Must select which hospital to manage
- Full administrative access to selected hospital

#### **Single Hospital Users (Most Staff)**
```
Login → Auto-assigned to their hospital → Direct to Dashboard
```
- ADMIN, RECEPTIONIST, ACCOUNTANT, etc.
- Automatically use their assigned hospital
- No selection needed - seamless experience

#### **Multi-Hospital Users (Doctors/Nurses)**
```
Login → Check affiliations → Multiple hospitals? → Hospital Selection → Choose working hospital → Dashboard
```
- Doctors/nurses working at 2+ hospitals
- Must select which hospital they're working at today
- Different roles/permissions at different hospitals

### 2. **Multi-Hospital Affiliation System**

#### **New Model: UserHospitalAffiliation**
```python
class UserHospitalAffiliation(models.Model):
    user = models.ForeignKey('User', related_name='hospital_affiliations')
    hospital = models.ForeignKey('Hospital', related_name='affiliated_users')
    
    # Role and department at this specific hospital
    role_at_hospital = models.CharField(max_length=20, choices=User.ROLE_CHOICES)
    department = models.ForeignKey('Department', null=True, blank=True)
    
    # Status
    is_primary = models.BooleanField(default=False)  # Main workplace
    is_active = models.BooleanField(default=True)
    
    # Specific permissions at this hospital
    can_access_billing = models.BooleanField(default=False)
    can_access_pharmacy = models.BooleanField(default=False)
    can_access_lab = models.BooleanField(default=False)
    can_access_radiology = models.BooleanField(default=False)
    
    # Employment details
    employee_id_at_hospital = models.CharField(max_length=50, blank=True)
    working_days = models.JSONField(default=list)
    working_hours = models.JSONField(default=dict)
```

#### **Enhanced User Model Methods**
```python
class User(AbstractUser):
    def get_hospitals(self):
        """Get all hospitals this user works at"""
        return Hospital.objects.filter(
            affiliated_users__user=self,
            affiliated_users__is_active=True
        ).distinct()
    
    def get_primary_hospital(self):
        """Get user's main hospital"""
        affiliation = self.hospital_affiliations.filter(
            is_primary=True, is_active=True
        ).first()
        return affiliation.hospital if affiliation else self.hospital
    
    def get_hospital_role(self, hospital):
        """Get user's role at specific hospital"""
        affiliation = self.hospital_affiliations.get(
            hospital=hospital, is_active=True
        )
        return affiliation.role_at_hospital
    
    def can_access_hospital(self, hospital):
        """Check if user can access specific hospital"""
        if self.role == 'SUPERADMIN':
            return True
        return self.hospital_affiliations.filter(
            hospital=hospital, is_active=True
        ).exists()
```

### 3. **Real-World Example: Dr. Ahmed**

**Scenario:** Dr. Ahmed works at 3 hospitals with same email/phone:

```python
# Dr. Ahmed's Profile
user = User.objects.create(
    email="dr.ahmed@email.com",
    phone="+1234567890",
    first_name="Ahmed",
    last_name="Hassan",
    role="DOCTOR"  # Base role
)

# Hospital Affiliations
UserHospitalAffiliation.objects.create(
    user=user,
    hospital=city_hospital,
    role_at_hospital="DOCTOR",
    department=cardiology_dept,
    is_primary=True,  # Main workplace
    working_days=["Monday", "Tuesday", "Wednesday"],
    can_access_billing=True
)

UserHospitalAffiliation.objects.create(
    user=user,
    hospital=private_clinic,
    role_at_hospital="CONSULTANT",
    department=cardiology_private,
    working_days=["Thursday", "Friday"],
    can_access_billing=False  # Different permissions
)

UserHospitalAffiliation.objects.create(
    user=user,
    hospital=emergency_center,
    role_at_hospital="EMERGENCY_DOCTOR",
    working_days=["Saturday"],
    can_access_lab=True,
    can_access_radiology=True
)
```

**Dr. Ahmed's Login Experience:**
1. Logs in with `dr.ahmed@email.com`
2. System detects 3 hospital affiliations
3. Redirected to hospital selection page showing:
   - **City Hospital** (Primary) - Role: Doctor
   - **Private Clinic** - Role: Consultant  
   - **Emergency Center** - Role: Emergency Doctor
4. Selects "City Hospital"
5. Dashboard loads with City Hospital's patients/data
6. Navigation shows "Dr. Ahmed @ City Hospital (Doctor)"

### 4. **Enhanced Middleware Logic**

```python
def process_request(self, request):
    if request.user.role == 'SUPERADMIN':
        # SUPERADMIN hospital selection flow
        # Can access any hospital
        
    elif request.user.has_multiple_hospitals():
        # Multi-hospital user flow
        hospital_id = request.session.get('selected_hospital_id')
        if hospital_id:
            # Verify user can access this hospital
            if request.user.can_access_hospital(hospital):
                request.hospital = hospital
                request.hospital_role = request.user.get_hospital_role(hospital)
            else:
                # Redirect to hospital selection
                return redirect('accounts:multi_hospital_selection')
        else:
            # No hospital selected - redirect to selection
            return redirect('accounts:multi_hospital_selection')
            
    else:
        # Single hospital user - auto-assign
        request.hospital = request.user.hospital
```

### 5. **Hospital Selection Interface**

#### **For SUPERADMINs:**
- Shows ALL active hospitals
- Hospital cards with system statistics
- Full administrative access to any hospital

#### **For Multi-Hospital Users:**
- Shows ONLY their affiliated hospitals
- Hospital cards show their role at each hospital
- Different permissions at each hospital
- Primary hospital highlighted

### 6. **Navigation Enhancement**

```html
<!-- Hospital Selector Component -->
{% if user.role == 'SUPERADMIN' %}
    <!-- Show current hospital + switch option -->
    <div class="hospital-selector">
        <span class="badge bg-primary">SUPERADMIN</span>
        {{ current_hospital.name }}
        <a href="{% url 'accounts:hospital_selection' %}">Switch</a>
    </div>
{% elif user.has_multiple_hospitals %}
    <!-- Show current hospital + role + switch option -->
    <div class="hospital-selector">
        {{ current_hospital.name }}
        <small>({{ user.get_hospital_role }})</small>
        <a href="{% url 'accounts:multi_hospital_selection' %}">Switch</a>
    </div>
{% else %}
    <!-- Single hospital - just show name -->
    <div class="hospital-info">
        {{ user.hospital.name }}
    </div>
{% endif %}
```

### 7. **Patient Views Enhancement**

Now the patient views need to be updated to work with multi-hospital context:

```python
class PatientListView(RoleBasedPermissionMixin, HospitalFilterMixin, ListView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Use request.hospital instead of request.user.hospital
        hospital = getattr(self.request, 'hospital', self.request.user.hospital)
        
        context['total_patients'] = Patient.objects.filter(
            hospital=hospital,  # Use current selected hospital
            is_active=True
        ).count()
        
        return context
```

### 8. **Security and Permissions**

#### **Access Control:**
- SUPERADMINs: Full access to any hospital
- Multi-hospital users: Only their affiliated hospitals
- Single hospital users: Only their assigned hospital
- Role-based permissions at each hospital

#### **Data Isolation:**
- All queries filtered by selected hospital
- Session-based hospital context
- Automatic permission checking

### 9. **Real-World Benefits**

#### **For Hospitals:**
- ✅ Doctors can work at multiple branches
- ✅ Shared staff between partner hospitals
- ✅ Consultants with multiple affiliations
- ✅ Different roles at different locations

#### **For Users:**
- ✅ Single login for all hospitals
- ✅ Role-specific permissions per hospital
- ✅ Clear indication of current working hospital
- ✅ Easy switching between hospitals

#### **For System:**
- ✅ Proper data isolation between hospitals
- ✅ Flexible permission management
- ✅ Scalable for hospital networks
- ✅ Maintains single user identity

### 10. **Implementation Status**

✅ **Fixed Hospital Selection** - Removed `is_active` field error
✅ **Enhanced Middleware** - Handles multi-hospital users  
✅ **Multi-Hospital Views** - Selection interface for complex users
✅ **User Model Enhancement** - Methods for hospital management
✅ **Navigation Integration** - Shows current hospital and role
✅ **Security Implementation** - Proper access control

### 🎯 **User Experience Summary**

1. **Simple Users** (receptionist, admin): Direct login → their hospital
2. **Multi-Hospital Users** (doctors, nurses): Login → select hospital → dashboard  
3. **SUPERADMINs**: Login → select any hospital → full access

This system now handles the real-world complexity of healthcare staffing while maintaining security and usability!
