# 🏥 HMS SUPER ADMIN GUIDE - Multi-Tenant Database Management

## 📊 **SUPER ADMIN DATABASE ACCESS OVERVIEW**

### **How Super Admin Works in HMS Multi-Tenant System**

The HMS uses a **multi-tenant architecture** where each hospital has its own separate database. As a super admin, you have access to:

1. **Main System Database** (`db.sqlite3`) - Contains tenant information and super admin accounts
2. **Individual Hospital Databases** (`hospital_*`) - Each hospital's operational data

---

## 🔑 **DATABASE STRUCTURE EXPLANATION**

### **Main System Database** (`db.sqlite3`)
Contains:
- **Tenant Management**: Hospital registration and configuration
- **Super Admin Accounts**: System administrators
- **Global Settings**: System-wide configurations

### **Hospital Databases** (`hospital_3262662`, `hospital_2210`, etc.)
Each contains:
- **Patients**: Hospital-specific patient records
- **Doctors**: Hospital staff and doctors
- **Appointments**: Scheduling data
- **Laboratory**: Lab tests and results
- **Billing**: Invoices and payments
- **EMR**: Electronic medical records
- **All other modules**: Hospital-specific operational data

---

## 🎯 **HOW TO ACCESS DIFFERENT MODULES AS SUPER ADMIN**

### **Step 1: Understanding Your Current Access**
When you login as super admin, you initially access the **main system database**.

### **Step 2: Accessing Hospital Modules**
To use hospital-specific modules (patients, doctors, laboratory, etc.), you need to:

1. **Select a Hospital/Tenant**
2. **Switch to Hospital Database Context**
3. **Access Hospital Modules**

---

## 🚀 **SUPER ADMIN USAGE GUIDE**

### **Option 1: Direct Hospital Access (Recommended)**
```
URL Pattern: http://[hospital-subdomain].yourdomain.com/
Example: http://3262662.localhost:8000/
```

### **Option 2: Hospital Selection Interface**
```
1. Login as super admin
2. Go to tenant/hospital selection page
3. Choose hospital to manage
4. Access all modules within that hospital context
```

---

## 🛠 **FIXING THE CURRENT DATABASE ISSUES**

The errors you're seeing (`no such table: laboratory_labtest`, `no such table: patients_patient`) occur because:

1. **You're accessing hospital modules from the main database context**
2. **Hospital database tables don't exist in the main database**
3. **You need to access modules within a hospital context**

### **Solution: Create Hospital Access Interface**

Let me create a hospital selection interface for super admin:

---

## 🏥 **HOSPITAL/TENANT SELECTION SYSTEM**

### **Current Hospitals in System:**
- **Test Hospital** (Subdomain: 3262662, Database: hospital_3262662)

### **To Access Hospital Modules:**
1. Navigate to: `http://3262662.localhost:8000/` 
2. Or use hospital selection interface (I'll create this)

---

## 📋 **AVAILABLE MODULES PER HOSPITAL**

When you access a hospital context, you can use:

### **Core Hospital Modules:**
- 👥 **Patients Management** - `/patients/`
- 👨‍⚕️ **Doctors Management** - `/doctors/`
- 📅 **Appointments** - `/appointments/`
- 🧪 **Laboratory** - `/laboratory/`
- 💊 **Pharmacy** - `/pharmacy/`
- 📸 **Radiology** - `/radiology/`
- 💰 **Billing** - `/billing/`
- 📋 **EMR (Electronic Medical Records)** - `/emr/`
- 🏥 **IPD (In-Patient Department)** - `/ipd/`
- 🚨 **Emergency** - `/emergency/`
- 👩‍⚕️ **Nurses** - `/nurses/`
- 📊 **Reports** - `/reports/`

### **AI-Enhanced Modules:**
- 🤖 **AI Scheduling Dashboard** - `/appointments/ai/dashboard/`
- 🧠 **Clinical AI Dashboard** - `/emr/ai/dashboard/`
- 💡 **AI Billing Dashboard** - `/billing/ai/dashboard/`

---

## 🔧 **SUPER ADMIN SPECIFIC FEATURES**

### **System Management:**
- **Tenant/Hospital Management** - Add/edit hospitals
- **User Management** - Manage hospital admins
- **System Configuration** - Global settings
- **Database Management** - Backup/restore

### **Cross-Hospital Analytics:**
- **Multi-tenant reporting**
- **System-wide statistics**
- **Performance monitoring**

---

## 🚨 **CURRENT ISSUE RESOLUTION**

The laboratory error occurs because you're trying to access `/laboratory/` from the main database context. Here's how to fix it:

### **Immediate Fix:**
Access laboratory via hospital context: `http://3262662.localhost:8000/laboratory/`

### **Better Solution:**
I'll create a hospital selection interface for easy switching between hospitals.

---

## 🎯 **RECOMMENDED WORKFLOW FOR SUPER ADMIN**

1. **Login as Super Admin**
2. **Access Hospital Selection Dashboard**
3. **Choose Hospital to Manage**
4. **Use All Hospital Modules**
5. **Switch Between Hospitals as Needed**
6. **Return to System Management When Required**

---

Would you like me to create:
1. **Hospital Selection Interface** for easy hospital switching?
2. **Super Admin Dashboard** with multi-tenant overview?
3. **Direct hospital access URLs** for your current hospitals?

The key point is: **Each hospital has its own database, so you need to access modules within the hospital context, not from the main system database.**
