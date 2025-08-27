#!/usr/bin/env python3
"""
Comprehensive fix script to replace all request.user.tenant references
"""
import re
import os

def fix_tenant_references(file_path):
    """Fix all tenant references in a file"""
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    print(f"🔧 Fixing {file_path}...")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Common replacements
    replacements = [
        # Fix form instantiations
        (r'(\w+Form\([^)]*?)tenant=request\.user\.tenant([^)]*\))', 
         r'\1hospital=request.session.get("selected_hospital_code")\2'),
        
        (r'(\w+Form\([^)]*?)tenant=self\.request\.user\.tenant([^)]*\))', 
         r'\1hospital=self.request.session.get("selected_hospital_code")\2'),
        
        # Fix kwargs assignments
        (r"kwargs\['tenant'\] = request\.user\.tenant", 
         r"kwargs['hospital'] = request.session.get('selected_hospital_code')"),
        
        (r"kwargs\['tenant'\] = self\.request\.user\.tenant", 
         r"kwargs['hospital'] = self.request.session.get('selected_hospital_code')"),
        
        # Fix form.instance assignments (these should be removed since tenant field is commented out)
        (r'form\.instance\.tenant = request\.user\.tenant', 
         r'# form.instance.tenant = request.user.tenant  # Temporarily commented out'),
        
        (r'form\.instance\.tenant = self\.request\.user\.tenant', 
         r'# form.instance.tenant = self.request.user.tenant  # Temporarily commented out'),
        
        # Fix object assignments
        (r'(\w+)\.tenant = request\.user\.tenant', 
         r'# \1.tenant = request.user.tenant  # Temporarily commented out'),
        
        (r'(\w+)\.tenant = self\.request\.user\.tenant', 
         r'# \1.tenant = self.request.user.tenant  # Temporarily commented out'),
        
        # Fix object filtering (temporarily remove tenant filters)
        (r'\.filter\(([^)]*?)tenant=request\.user\.tenant,?\s*([^)]*)\)', 
         r'.filter(\1\2)'),
        
        (r'\.filter\(([^)]*?)tenant=self\.request\.user\.tenant,?\s*([^)]*)\)', 
         r'.filter(\1\2)'),
        
        # Fix .get() calls
        (r'\.get\(([^)]*?)tenant=request\.user\.tenant,?\s*([^)]*)\)', 
         r'.get(\1\2)'),
        
        (r'\.get\(([^)]*?)tenant=self\.request\.user\.tenant,?\s*([^)]*)\)', 
         r'.get(\1\2)'),
    ]
    
    # Apply replacements
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    # Clean up any double commas or leading/trailing commas that might have been created
    content = re.sub(r',\s*,', ',', content)  # Remove double commas
    content = re.sub(r'\(\s*,', '(', content)  # Remove leading comma
    content = re.sub(r',\s*\)', ')', content)  # Remove trailing comma
    
    # Write back if changed
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"   ✅ Updated with tenant reference fixes")
        return True
    else:
        print(f"   ℹ️ No changes needed")
        return False

def main():
    """Main function to fix all tenant references"""
    
    print("🔧 HMS Tenant Reference Fix Tool")
    print("=" * 50)
    
    # Files to fix
    files_to_fix = [
        "/home/mehedi/Projects/zain_hms/apps/appointments/views.py",
        "/home/mehedi/Projects/zain_hms/apps/patients/views.py",
        "/home/mehedi/Projects/zain_hms/apps/patients/models.py",
    ]
    
    fixed_count = 0
    
    for file_path in files_to_fix:
        if fix_tenant_references(file_path):
            fixed_count += 1
    
    print(f"\n🎉 Fixed {fixed_count} files")
    print("💡 Note: Tenant fields are temporarily commented out")
    print("   These fixes will work until the tenant system is fully implemented")

if __name__ == "__main__":
    main()
