# apps/tenants/context_processors.py
"""
Context processors for hospital/tenant information
Makes hospital context available in all templates
"""

def hospital_context(request):
    """
    Add hospital context to all templates
    Best practice for SaaS multi-tenant applications
    """
    context = {}
    
    if request.user.is_authenticated:
        # Get current hospital
        current_hospital = request.user.get_current_hospital()
        
        if current_hospital:
            context.update({
                'current_hospital': current_hospital,
                'hospital_enabled_modules': current_hospital.get_enabled_modules(),
                'hospital_subscription_active': current_hospital.is_subscription_active,
                'hospital_is_trial': current_hospital.is_trial,
                'hospital_days_left': current_hospital.days_until_expiry,
                'user_role_in_hospital': request.user.get_role_in_hospital(current_hospital),
            })
        
        # Get all hospitals user has access to
        user_hospitals = request.user.get_hospitals()
        context.update({
            'user_hospitals': user_hospitals,
            'has_multiple_hospitals': user_hospitals.count() > 1,
        })
        
        # Add session context for hospital switching
        if hasattr(request, 'session'):
            context.update({
                'hospital_switch_time': request.session.get('hospital_switch_time'),
                'remembered_hospital_id': request.session.get('remember_hospital'),
            })
    
    return context


def user_permissions(request):
    """
    Add user permission context for module access control
    """
    context = {}
    
    if request.user.is_authenticated:
        current_hospital = request.user.get_current_hospital()
        
        if current_hospital:
            # Module access permissions
            module_access = {}
            modules = ['appointments', 'patients', 'telemedicine', 'laboratory', 
                      'radiology', 'billing', 'pharmacy', 'emergency', 'ipd']
            
            for module in modules:
                # Check if user has role permission AND hospital has module enabled
                has_role_permission = request.user.has_module_permission(module)
                module_enabled = getattr(current_hospital, f'{module}_enabled', True)
                module_access[f'can_access_{module}'] = has_role_permission and module_enabled
            
            context.update(module_access)
            
            # Add hospital admin permissions
            context.update({
                'is_hospital_admin': request.user.role == 'HOSPITAL_ADMIN',
                'can_manage_hospital': request.user.role in ['HOSPITAL_ADMIN', 'SUPERADMIN'],
                'can_view_analytics': request.user.role in ['HOSPITAL_ADMIN', 'DOCTOR', 'ACCOUNTANT'],
                'can_manage_users': request.user.role == 'HOSPITAL_ADMIN',
            })
    
    return context
