from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_GET, require_POST
from django.utils import timezone
from apps.patients.models import Patient
from apps.appointments.models import Appointment
from django.db import models
from django.db.models import Count, Sum
from django.core.cache import cache
from datetime import timedelta

CACHE_TIMEOUT = 300  # 5 minutes

@require_GET
def dashboard_metrics_api(request):
    """ZAIN HMS unified dashboard metrics API"""
    cache_key = "api_metrics::zain_hms"
    data = cache.get(cache_key)
    
    if not data:
        today = timezone.localdate()
        start_today = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))
        
        # Get unified metrics for ZAIN HMS
        total_patients = Patient.objects.count()
        total_appointments = Appointment.objects.count()
        patients_today = Patient.objects.filter(registration_date__gte=start_today).count()
        appointments_today = Appointment.objects.filter(appointment_date=today).count()
        
        # Revenue calculation
        revenue_today = Appointment.objects.filter(
            appointment_date=today,
            status__in=['COMPLETED', 'CHECKED_IN', 'IN_PROGRESS']
        ).exclude(consultation_fee=0).aggregate(
            total=Sum('consultation_fee')
        )['total'] or 0.0
        
        # Doctor utilization (top 5 doctors today)
        doctor_utilization = []
        try:
            doctor_stats = (Appointment.objects.filter(appointment_date=today)
                .values('doctor__first_name', 'doctor__last_name')
                .annotate(appointments=Count('id'))
                .order_by('-appointments')[:5])
            
            for d in doctor_stats:
                doctor_utilization.append({
                    'name': f"{d['doctor__first_name']} {d['doctor__last_name']}",
                    'appointments': d['appointments']
                })
        except Exception:
            pass
        
        data = {
            'total_patients': total_patients,
            'total_appointments': total_appointments,
            'patients_today': patients_today,
            'appointments_today': appointments_today,
            'revenue_today': float(revenue_today),
            'occupancy': [{'name': 'ZAIN HMS', 'patients': total_patients}],
            'doctor_utilization': doctor_utilization,
            'timestamp': timezone.now().isoformat(),
            'is_superuser': bool(request.user.is_superuser) if request.user.is_authenticated else False,
            'user_preferences': {
                'theme': getattr(request.user, 'theme_preference', None) if request.user.is_authenticated else None,
                'currency': getattr(request.user, 'currency_preference', None) if request.user.is_authenticated else None,
            }
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, data, CACHE_TIMEOUT)
    
    return JsonResponse(data)

@require_POST
def save_user_preferences(request):
    if not request.user.is_authenticated:
        return HttpResponseBadRequest('Authentication required')
    theme = request.POST.get('theme')
    currency = request.POST.get('currency')
    changed = False
    if theme in ['dark','light','flat','teal','slate','neutral']:
        request.user.theme_preference = theme
        changed = True
    if currency and len(currency) <= 10:
        request.user.currency_preference = currency.upper()
        changed = True
    if changed:
        request.user.save(update_fields=['theme_preference','currency_preference'])
    return JsonResponse({'ok': True, 'theme': request.user.theme_preference, 'currency': request.user.currency_preference})
