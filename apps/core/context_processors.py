# apps/core/context_processors.py
from django.db.models import Count, Q
from django.utils import timezone
from apps.accounts.models import Hospital
from apps.core.models import Notification, SystemConfiguration
from apps.appointments.models import Appointment
from apps.emergency.models import EmergencyCase
from apps.patients.models import Patient


def hospital_context(request):
    """Add hospital context to all templates"""
    context = {}
    
    if hasattr(request, 'user') and request.user.is_authenticated:
        hospital = getattr(request, 'hospital', None) or request.user.hospital
        
        if hospital:
            context.update({
                'hospital': hospital,
                'hospital_name': hospital.name,
                'hospital_logo': hospital.logo,
            })
            
            # Get or create system configuration
            try:
                system_config = SystemConfiguration.objects.get(hospital=hospital)
                context['system_config'] = system_config
                context['currency_code'] = system_config.currency_code
                context['hospital_phone'] = system_config.contact_phone
                context['hospital_email'] = system_config.contact_email
            except SystemConfiguration.DoesNotExist:
                # Create default configuration
                system_config = SystemConfiguration.objects.create(
                    hospital=hospital,
                    hospital_name=hospital.name,
                    contact_email=hospital.email,
                    contact_phone=hospital.phone,
                    address=hospital.address
                )
                context['system_config'] = system_config
                context['currency_code'] = 'USD'
                context['hospital_phone'] = hospital.phone
                context['hospital_email'] = hospital.email
    
    return context


def notifications_context(request):
    """Add notification context to all templates"""
    context = {
        'unread_notifications_count': 0,
        'recent_notifications': [],
        'urgent_notifications': [],
    }
    
    if hasattr(request, 'user') and request.user.is_authenticated:
        hospital = getattr(request, 'hospital', None) or request.user.hospital
        
        if hospital:
            # Get unread notifications count
            unread_count = Notification.objects.filter(
                recipient=request.user,
                hospital=hospital,
                is_read=False
            ).count()
            
            # Get recent notifications (last 5)
            recent_notifications = Notification.objects.filter(
                recipient=request.user,
                hospital=hospital
            ).order_by('-created_at')[:5]
            
            # Get urgent notifications
            urgent_notifications = Notification.objects.filter(
                recipient=request.user,
                hospital=hospital,
                priority='URGENT',
                is_read=False
            ).order_by('-created_at')[:3]
            
            context.update({
                'unread_notifications_count': unread_count,
                'recent_notifications': recent_notifications,
                'urgent_notifications': urgent_notifications,
            })
    
    return context


def dashboard_stats_context(request):
    """Add quick dashboard stats to all templates"""
    context = {}
    
    if hasattr(request, 'user') and request.user.is_authenticated:
        hospital = getattr(request, 'hospital', None) or request.user.hospital
        user = request.user
        
        if hospital:
            today = timezone.now().date()
            
            # Common stats for all users
            context['today'] = today
            
            # Role-specific quick stats in header
            if user.role in ['ADMIN', 'SUPERADMIN'] or user.is_superuser:
                context.update({
                    'quick_stats': {
                        'patients_today': Patient.objects.filter(
                            hospital=hospital, 
                            created_at__date=today
                        ).count(),
                        'appointments_today': Appointment.objects.filter(
                            hospital=hospital, 
                            appointment_date=today
                        ).count(),
                        'emergency_cases_active': EmergencyCase.objects.filter(
                            hospital=hospital, 
                            status__in=['WAITING', 'IN_PROGRESS']
                        ).count(),
                    }
                })
            
            elif user.role == 'DOCTOR':
                context.update({
                    'quick_stats': {
                        'my_appointments_today': Appointment.objects.filter(
                            doctor=user,
                            hospital=hospital, 
                            appointment_date=today
                        ).count(),
                        'pending_appointments': Appointment.objects.filter(
                            doctor=user,
                            hospital=hospital, 
                            status='SCHEDULED'
                        ).count(),
                    }
                })
            
            elif user.role in ['NURSE', 'RECEPTIONIST']:
                context.update({
                    'quick_stats': {
                        'appointments_today': Appointment.objects.filter(
                            hospital=hospital, 
                            appointment_date=today
                        ).count(),
                        'emergency_cases_active': EmergencyCase.objects.filter(
                            hospital=hospital, 
                            status__in=['WAITING', 'IN_PROGRESS']
                        ).count(),
                    }
                })
    
    return context


def user_permissions_context(request):
    """Add user permissions context"""
    context = {
        'user_permissions': {},
        'user_role': None,
        'is_admin': False,
        'is_doctor': False,
        'is_nurse': False,
        'is_receptionist': False,
        'can_manage_users': False,
        'can_view_reports': False,
    }
    
    if hasattr(request, 'user') and request.user.is_authenticated:
        user = request.user
        
        # Set role flags
        context['user_role'] = user.role
        context['is_admin'] = user.role in ['ADMIN', 'SUPERADMIN'] or user.is_superuser
        context['is_doctor'] = user.role == 'DOCTOR'
        context['is_nurse'] = user.role == 'NURSE'
        context['is_receptionist'] = user.role == 'RECEPTIONIST'
        
        # Set permission flags
        context['can_manage_users'] = user.role in ['ADMIN', 'SUPERADMIN'] or user.is_superuser
        context['can_view_reports'] = user.role in ['ADMIN', 'SUPERADMIN', 'DOCTOR', 'ACCOUNTANT'] or user.is_superuser
        
        # Module permissions
        modules = [
            'patients', 'appointments', 'doctors', 'nurses', 'billing', 
            'pharmacy', 'laboratory', 'emergency', 'inventory', 'reports',
            'analytics', 'hr', 'surgery', 'telemedicine'
        ]
        
        user_permissions = {}
        for module in modules:
            user_permissions[f'can_access_{module}'] = user.has_module_permission(module)
        
        context['user_permissions'] = user_permissions
    
    return context


def navigation_context(request):
    """Add navigation context for sidebar menu"""
    context = {
        'navigation_items': [],
        'active_module': None,
    }
    
    if hasattr(request, 'user') and request.user.is_authenticated:
        user = request.user
        
        # Determine active module from current path
        path_parts = request.path.strip('/').split('/')
        if path_parts:
            context['active_module'] = path_parts[0]
        
        # Build navigation based on user permissions
        navigation_items = []
        
        # Dashboard (always available)
        navigation_items.append({
            'name': 'Dashboard',
            'url': '/dashboard/',
            'icon': 'fas fa-tachometer-alt',
            'active': context['active_module'] == 'dashboard'
        })
        
        # Patients
        if user.has_module_permission('patients'):
            navigation_items.append({
                'name': 'Patients',
                'url': '/patients/',
                'icon': 'fas fa-user-injured',
                'active': context['active_module'] == 'patients'
            })
        
        # Appointments
        if user.has_module_permission('appointments'):
            navigation_items.append({
                'name': 'Appointments',
                'url': '/appointments/',
                'icon': 'fas fa-calendar-check',
                'active': context['active_module'] == 'appointments'
            })
        
        # Doctors
        if user.has_module_permission('doctors'):
            navigation_items.append({
                'name': 'Doctors',
                'url': '/doctors/',
                'icon': 'fas fa-user-md',
                'active': context['active_module'] == 'doctors'
            })
        
        # Emergency
        if user.has_module_permission('emergency'):
            navigation_items.append({
                'name': 'Emergency',
                'url': '/emergency/',
                'icon': 'fas fa-ambulance',
                'active': context['active_module'] == 'emergency',
                'badge': 'urgent'
            })
        
        # Billing
        if user.has_module_permission('billing'):
            navigation_items.append({
                'name': 'Billing',
                'url': '/billing/',
                'icon': 'fas fa-file-invoice-dollar',
                'active': context['active_module'] == 'billing'
            })
        
        # Pharmacy
        if user.has_module_permission('pharmacy'):
            navigation_items.append({
                'name': 'Pharmacy',
                'url': '/pharmacy/',
                'icon': 'fas fa-pills',
                'active': context['active_module'] == 'pharmacy'
            })
        
        # Laboratory
        if user.has_module_permission('laboratory'):
            navigation_items.append({
                'name': 'Laboratory',
                'url': '/laboratory/',
                'icon': 'fas fa-microscope',
                'active': context['active_module'] == 'laboratory'
            })
        
        # Inventory
        if user.has_module_permission('inventory'):
            navigation_items.append({
                'name': 'Inventory',
                'url': '/inventory/',
                'icon': 'fas fa-boxes',
                'active': context['active_module'] == 'inventory'
            })
        
        # Reports (Admin users)
        if user.has_module_permission('reports'):
            navigation_items.append({
                'name': 'Reports',
                'url': '/reports/',
                'icon': 'fas fa-chart-bar',
                'active': context['active_module'] == 'reports'
            })
        
        context['navigation_items'] = navigation_items
    
    return context
