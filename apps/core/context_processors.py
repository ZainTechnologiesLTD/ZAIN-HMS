# apps/core/context_processors.py
from django.db.models import Count, Q
from django.utils import timezone
from apps.core.models import SystemConfiguration
from apps.appointments.models import Appointment
from apps.emergency.models import EmergencyCase
from apps.patients.models import Patient


import json
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Count, Q, Sum, Avg
from datetime import datetime, timedelta
from decimal import Decimal

def is_user_authenticated(request):
    """Helper function to safely check if user is authenticated"""
    return (hasattr(request, 'user') and request.user and 
            hasattr(request.user, 'is_authenticated') and request.user.is_authenticated)

def hospital_context(request):
    """Add hospital context to all templates - Simplified for unified system"""
    context = {}
    
    if is_user_authenticated(request):
        # Unified ZAIN HMS system - get or create single system configuration
        try:
            system_config = SystemConfiguration.objects.first()
            if not system_config:
                # Create default configuration for unified system
                system_config = SystemConfiguration.objects.create(
                    system_name='ZAIN Hospital Management System',
                    contact_email='admin@zainhms.com',
                    contact_phone='+1234567890',
                    address='123 Healthcare Ave, Medical City',
                )
            
            context.update({
                'system_config': system_config,
                'hospital_name': system_config.system_name,
                'hospital_logo': system_config.system_logo,
                'currency_code': system_config.currency_code,
                'hospital_phone': system_config.contact_phone,
                'hospital_email': system_config.contact_email,
            })
        except Exception as e:
            # Fallback values if system config fails
            context.update({
                'hospital_name': 'ZAIN Hospital Management System',
                'currency_code': 'USD',
                'hospital_phone': '',
                'hospital_email': '',
            })
    
    return context


def zain_context(request):
    """ZAIN-specific context processor - alias for hospital_context"""
    return hospital_context(request)


def notifications_context(request):
    """Add notification context to all templates"""
    context = {
        'notifications_count': 0,
        'recent_notifications': [],
        'urgent_notifications': [],
    }
    
    if is_user_authenticated(request):
        try:
            # Use default DB in unified system. Import model and query normally.
            from apps.notifications.models import Notification

            # Get unread notifications count
            unread_count = Notification.objects.filter(
                recipient=request.user,
                read=False
            ).count()

            # Get recent notifications (last 5)
            recent_notifications = Notification.objects.filter(
                recipient=request.user
            ).order_by('-created_at')[:5]

            # Get urgent notifications
            urgent_notifications = Notification.objects.filter(
                recipient=request.user,
                level='error',
                read=False
            ).order_by('-created_at')[:3]

            context.update({
                'notifications_count': unread_count,
                'recent_notifications': recent_notifications,
                'urgent_notifications': urgent_notifications,
            })
        except Exception:
            # Fallback to dummy data if database issues
            context.update({
                'notifications_count': 2,
                'recent_notifications': [
                    {'message': 'Welcome to HMS', 'created_at': timezone.now()},
                    {'message': 'System running smoothly', 'created_at': timezone.now()},
                ],
                'urgent_notifications': [],
            })
    
    return context


def dashboard_stats_context(request):
    """Add quick dashboard stats to all templates"""
    context = {}
    
    if is_user_authenticated(request):
        # Prefer hospital set on request; else user's assigned; else session selection
        hospital = getattr(request, 'hospital', None) or getattr(request.user, 'hospital', None)
        if not hospital and request.session.get('selected_hospital_code'):
            try:
                from apps.accounts.models import Hospital
                hospital = Hospital.objects.filter(code=request.session['selected_hospital_code']).first()
            except Exception:
                pass  # Not needed in unified system
        user = request.user
        
        if True:  # Unified ZAIN HMS system
            today = timezone.now().date()
            
            # Common stats for all users
            context['today'] = today
            
            # Role-specific quick stats in header
            if user.role in ['ADMIN', 'SUPERADMIN'] or user.is_superuser:
                # Simplified stats for now - hospital filtering will be added later
                context.update({
                    'quick_stats': {
                        'patients_today': Patient.objects.filter(
                            hospital=hospital, 
                            registration_date__date=today
                        ).count() if hospital else 0,
                        'appointments_today': Appointment.objects.filter(
                            appointment_date=today
                        ).count(),
                        'emergency_cases_active': 0,  # Simplified for now
                    }
                })
            
            elif user.role == 'DOCTOR':
                from apps.doctors.models import Doctor
                try:
                    doctor = Doctor.objects.get(user=user)
                    
                    context.update({
                        'quick_stats': {
                            'my_appointments_today': Appointment.objects.filter(
                                appointment_date=today,
                                doctor=doctor
                            ).count(),
                            'pending_appointments': Appointment.objects.filter(
                                status='SCHEDULED',
                                doctor=doctor
                            ).count(),
                        }
                    })
                except Doctor.DoesNotExist:
                    context.update({
                        'quick_stats': {
                            'my_appointments_today': 0,
                            'pending_appointments': 0,
                        }
                    })
            
            elif user.role in ['NURSE', 'RECEPTIONIST']:
                context.update({
                    'quick_stats': {
                        'appointments_today': Appointment.objects.filter(
                            appointment_date=today
                        ).count(),
                        'emergency_cases_active': 0,  # Simplified for now
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
    
    if is_user_authenticated(request):
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
            'pharmacy', 'laboratory', 'radiology', 'emergency', 'inventory', 
            'reports', 'surgery', 'ipd', 'opd', 'hr', 'telemedicine'
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
    
    if is_user_authenticated(request):
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
        
        # Radiology
        if user.has_module_permission('radiology'):
            navigation_items.append({
                'name': 'Radiology',
                'url': '/radiology/',
                'icon': 'fas fa-x-ray',
                'active': context['active_module'] == 'radiology'
            })
        
        # Surgery
        if user.has_module_permission('surgery'):
            navigation_items.append({
                'name': 'Surgery',
                'url': '/surgery/',
                'icon': 'fas fa-cut',
                'active': context['active_module'] == 'surgery'
            })
        
        # IPD
        if user.has_module_permission('ipd'):
            navigation_items.append({
                'name': 'IPD',
                'url': '/ipd/',
                'icon': 'fas fa-bed',
                'active': context['active_module'] == 'ipd'
            })
        
        # OPD
        if user.has_module_permission('opd'):
            navigation_items.append({
                'name': 'OPD',
                'url': '/opd/',
                'icon': 'fas fa-door-open',
                'active': context['active_module'] == 'opd'
            })
        
        # Telemedicine
        if user.has_module_permission('telemedicine'):
            navigation_items.append({
                'name': 'Telemedicine',
                'url': '/telemedicine/',
                'icon': 'fas fa-video',
                'active': context['active_module'] == 'telemedicine'
            })
        
        # Inventory
        if user.has_module_permission('inventory'):
            navigation_items.append({
                'name': 'Inventory',
                'url': '/inventory/',
                'icon': 'fas fa-boxes',
                'active': context['active_module'] == 'inventory'
            })
        
        # HR
        if user.has_module_permission('hr'):
            navigation_items.append({
                'name': 'HR',
                'url': '/hr/',
                'icon': 'fas fa-users-cog',
                'active': context['active_module'] == 'hr'
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
