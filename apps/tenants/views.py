from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from .models import Tenant, TenantAccess
from apps.accounts.models import CustomUser


def _log_hospital_switch(user, previous_hospital, new_hospital, request):
    """Log hospital context switches for audit purposes"""
    try:
        from apps.core.models import ActivityLog
        ActivityLog.objects.create(
            user=user,
            action='HOSPITAL_SWITCH',
            description=f'Switched from {previous_hospital.name if previous_hospital else "None"} to {new_hospital.name}',
            ip_address=_get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            hospital=new_hospital,
        )
    except Exception as e:
        # Don't fail the request if logging fails
        pass

def _get_client_ip(request):
    """Get client IP address for audit logging"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
def hospital_selection(request):
    """
    Enhanced hospital selection with SaaS best practices:
    1. Context switching with session management
    2. Last accessed hospital memory
    3. Hospital access validation 
    4. Audit logging for compliance
    """
    user = request.user
    
    # Get all hospitals user has access to with detailed info
    hospital_accesses = TenantAccess.objects.filter(
        user=user, 
        is_active=True
    ).select_related('tenant').order_by('-last_accessed', 'tenant__name')
    
    # If user has no hospital access, show appropriate message
    if not hospital_accesses.exists():
        if user.role == 'HOSPITAL_ADMIN':
            messages.error(request, 'No hospitals assigned to you. Please contact your system administrator.')
        else:
            messages.error(request, 'You do not have access to any hospitals. Please contact your hospital administrator.')
        context = {'hospital_accesses': [], 'current_hospital': None, 'user': user}
        return render(request, 'tenants/hospital_selection.html', context)
    
    # Auto-select if user has only one hospital (SaaS best practice)
    if hospital_accesses.count() == 1 and not user.hospital:
        single_access = hospital_accesses.first()
        # Persist selection to shared DB so other requests see the selection
        try:
            user.hospital = single_access.tenant
            user.save(using='default')
        except Exception:
            # Fallback: try regular save (don't block flow)
            try:
                user.hospital = single_access.tenant
                user.save()
            except Exception:
                pass
        single_access.last_accessed = timezone.now()
        single_access.save()
        
        messages.success(request, f'Automatically selected {single_access.tenant.name}')
        
        # Redirect to intended destination or dashboard
        next_url = request.GET.get('next', 'dashboard:dashboard')
        return redirect(next_url)
    
    if request.method == 'POST':
        hospital_id = request.POST.get('hospital_id')
        remember_choice = request.POST.get('remember_choice', False)
        
        if hospital_id:
            try:
                # Verify user has access to this hospital
                hospital_access = hospital_accesses.get(tenant_id=hospital_id)
                hospital = hospital_access.tenant
                
                # Validate hospital is active and not suspended
                if hasattr(hospital, 'is_suspended') and hospital.is_suspended:
                    messages.error(request, f'{hospital.name} is currently suspended. Please contact support.')
                    return redirect('tenants:hospital_selection')
                
                # Check subscription status (SaaS best practice)
                if not hospital.is_subscription_active and not hospital.is_trial:
                    messages.warning(request, f'{hospital.name} subscription has expired. Limited access may apply.')
                
                # Set current hospital for user
                previous_hospital = user.hospital
                # Persist selection to main DB explicitly
                try:
                    user.hospital = hospital
                    user.save(using='default')
                except Exception:
                    try:
                        user.hospital = hospital
                        user.save()
                    except Exception:
                        pass
                
                # Update last accessed time and access count
                hospital_access.last_accessed = timezone.now()
                if hasattr(hospital_access, 'access_count'):
                    hospital_access.access_count = (hospital_access.access_count or 0) + 1
                hospital_access.save()
                
                # Session management for context switching
                request.session['current_hospital_id'] = hospital.id
                request.session['hospital_switch_time'] = timezone.now().isoformat()
                
                if remember_choice:
                    request.session['remember_hospital'] = hospital.id
                
                # Audit logging for compliance (SaaS requirement)
                _log_hospital_switch(request.user, previous_hospital, hospital, request)
                
                messages.success(request, f'Successfully switched to {hospital.name}')
                
                # Smart redirect based on context
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                
                # Redirect based on user role and hospital capabilities
                if user.role == 'HOSPITAL_ADMIN':
                    return redirect('tenants:hospital_profile')
                elif user.role == 'DOCTOR' and hospital.telemedicine_enabled:
                    return redirect('telemedicine:dashboard')
                else:
                    return redirect('dashboard:dashboard')
                
            except TenantAccess.DoesNotExist:
                messages.error(request, 'You do not have access to this hospital.')
    
    # Prepare context with enhanced hospital information
    enhanced_accesses = []
    for access in hospital_accesses:
        hospital = access.tenant
        enhanced_accesses.append({
            'access': access,
            'hospital': hospital,
            'subscription_status': hospital.is_subscription_active,
            'is_trial': hospital.is_trial,
            'days_left': hospital.days_until_expiry,
            'enabled_modules': hospital.get_enabled_modules(),
            'user_count': hospital.get_user_count(),
            'last_accessed_friendly': access.last_accessed,
        })
    
    context = {
        'enhanced_accesses': enhanced_accesses,
        'hospital_accesses': hospital_accesses,  # Keep for backward compatibility
        'current_hospital': user.hospital,
        'user': user,
        'has_multiple_hospitals': hospital_accesses.count() > 1,
        'remembered_hospital': request.session.get('remember_hospital'),
    }
    
    return render(request, 'tenants/enhanced_hospital_selection.html', context)


@login_required
def switch_hospital(request, hospital_id):
    """Switch to a different hospital"""
    user = request.user
    
    try:
        # Verify user has access to this hospital
        hospital_access = TenantAccess.objects.get(user=user, tenant_id=hospital_id, is_active=True)
        hospital = hospital_access.tenant
        
        # Set current hospital for user and persist to shared DB
        try:
            user.hospital = hospital
            user.save(using='default')
        except Exception:
            try:
                user.hospital = hospital
                user.save()
            except Exception:
                pass
        
        # Update last accessed time
        hospital_access.last_accessed = timezone.now()
        hospital_access.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'hospital_name': hospital.name,
                'hospital_logo': hospital.logo.url if hospital.logo else None
            })
        
        messages.success(request, f'Successfully switched to {hospital.name}')
        return redirect(request.META.get('HTTP_REFERER', 'dashboard:dashboard'))
        
    except TenantAccess.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Access denied'})
        
        messages.error(request, 'You do not have access to this hospital.')
        return redirect('tenants:hospital_selection')


def get_hospital_context(user):
    """Get hospital context for templates"""
    if not user.is_authenticated:
        return {}
    
    current_hospital = user.get_current_hospital()
    hospital_accesses = user.get_hospitals()
    
    return {
        'current_hospital': current_hospital,
        'user_hospitals': hospital_accesses,
        'user_role_in_hospital': user.get_role_in_hospital(current_hospital) if current_hospital else None,
    }


@login_required
def hospital_profile(request):
    """View current hospital profile and settings"""
    current_hospital = request.user.get_current_hospital()

    # Fallback: some flows store selected hospital in session instead of
    # persisting to user.hospital. Try session lookup before redirecting.
    if not current_hospital:
        hid = request.session.get('current_hospital_id')
        if hid:
            try:
                current_hospital = Tenant.objects.using('default').get(id=hid)
            except Exception:
                current_hospital = None

    if not current_hospital:
        return redirect('tenants:hospital_selection')

    # Defensive calls: ensure missing helpers don't crash the view
    enabled_modules = []
    total_users = 0
    total_patients = 0
    subscription_status = getattr(current_hospital, 'is_subscription_active', False)

    try:
        enabled_modules = current_hospital.get_enabled_modules() if hasattr(current_hospital, 'get_enabled_modules') else []
    except Exception:
        enabled_modules = []

    try:
        total_users = current_hospital.get_user_count() if hasattr(current_hospital, 'get_user_count') else 0
    except Exception:
        total_users = 0

    try:
        total_patients = current_hospital.get_patient_count() if hasattr(current_hospital, 'get_patient_count') else 0
    except Exception:
        total_patients = 0

    context = {
        'hospital': current_hospital,
        'user_role': request.user.get_role_in_hospital(current_hospital),
        'page_title': 'Hospital Profile',
        'subscription_status': subscription_status,
        'enabled_modules': enabled_modules,
        'total_users': total_users,
        'total_patients': total_patients,
    }

    return render(request, 'tenants/hospital_profile.html', context)


@login_required
def subscription_details(request):
    """Subscription details and billing information"""
    current_hospital = request.user.get_current_hospital()
    
    if not current_hospital:
        messages.error(request, 'No hospital selected. Please select a hospital first.')
        return redirect('tenants:hospital_selection')
    
    # Calculate subscription metrics
    days_left = current_hospital.days_until_expiry
    is_trial = current_hospital.is_trial
    is_active = current_hospital.is_subscription_active
    
    # Usage statistics
    usage_stats = {
        'users': {
            'current': current_hospital.get_user_count(),
            'limit': current_hospital.max_users,
            'percentage': (current_hospital.get_user_count() / current_hospital.max_users * 100) if current_hospital.max_users > 0 else 0
        },
        'patients': {
            'current': current_hospital.get_patient_count(),
            'limit': current_hospital.max_patients,
            'percentage': (current_hospital.get_patient_count() / current_hospital.max_patients * 100) if current_hospital.max_patients > 0 else 0
        },
        'storage': {
            'current': current_hospital.get_storage_usage(),
            'limit': current_hospital.max_storage_gb,
            'percentage': (current_hospital.get_storage_usage() / current_hospital.max_storage_gb * 100) if current_hospital.max_storage_gb > 0 else 0
        }
    }
    
    context = {
        'hospital': current_hospital,
        'page_title': 'Subscription Details',
        'days_left': days_left,
        'is_trial': is_trial,
        'is_active': is_active,
        'usage_stats': usage_stats,
        'enabled_modules': current_hospital.get_enabled_modules(),
        'plan_features': current_hospital.get_plan_features(),
    }
    return render(request, 'tenants/subscription_details.html', context)


@login_required
def hospital_settings(request):
    """Hospital settings and module management"""
    current_hospital = request.user.get_current_hospital()
    
    if not current_hospital:
        messages.error(request, 'No hospital selected. Please select a hospital first.')
        return redirect('tenants:hospital_selection')
    
    context = {
        'hospital': current_hospital,
        'page_title': 'Hospital Settings',
        'enabled_modules': current_hospital.get_enabled_modules(),
        'all_modules': [
            {
                'name': 'appointments',
                'title': 'Appointments',
                'icon': 'fas fa-calendar-check',
                'description': 'Manage patient appointments and scheduling'
            },
            {
                'name': 'patients',
                'title': 'Patient Management',
                'icon': 'fas fa-user-injured',
                'description': 'Patient registration and medical records'
            },
            {
                'name': 'telemedicine',
                'title': 'Telemedicine',
                'icon': 'fas fa-video',
                'description': 'Video consultations and virtual care'
            },
            {
                'name': 'laboratory',
                'title': 'Laboratory',
                'icon': 'fas fa-flask',
                'description': 'Lab tests and results management'
            },
            {
                'name': 'radiology',
                'title': 'Radiology',
                'icon': 'fas fa-x-ray',
                'description': 'Medical imaging and reports'
            },
            {
                'name': 'billing',
                'title': 'Billing',
                'icon': 'fas fa-receipt',
                'description': 'Invoice and payment management'
            },
            {
                'name': 'pharmacy',
                'title': 'Pharmacy',
                'icon': 'fas fa-pills',
                'description': 'Medicine inventory and dispensing'
            }
        ]
    }
    return render(request, 'tenants/hospital_settings.html', context)
