# dashboard/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from apps.patients.models import Patient
from apps.appointments.models import Appointment
from apps.billing.models import Bill
# from apps.emergency.models import EmergencyCase  # Temporarily disabled due to table not existing
from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

@login_required
def dashboard_home(request):
    """Enhanced unified dashboard with real-time statistics"""
    today = timezone.now().date()
    user = request.user
    
    # Get hospital from session
    selected_hospital_id = request.session.get('selected_hospital_id')
    hospital = None
    
    if selected_hospital_id:
        try:
            from apps.tenants.models import Hospital
            hospital = Hospital.objects.get(id=selected_hospital_id)
        except:
            hospital = None
    
    context = {
        'today': today,
        'selected_hospital_id': selected_hospital_id,
        'hospital': hospital,
    }
    
    # Role-based dashboard data
    if user.role == 'HOSPITAL_ADMIN':
        # Hospital Admin gets specialized dashboard
        if selected_hospital_id:
            try:
                # Hospital-specific dashboard using correct database fields
                from django.db import connection

                # Prefer ORM count for portability and safety. Fall back to raw SQL only if ORM fails.
                try:
                    total_patients = Patient.objects.filter(hospital_id=selected_hospital_id, is_active=True).count()
                except Exception:
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute("SELECT COUNT(*) FROM patients_patient WHERE is_active = 1")
                            total_patients = cursor.fetchone()[0] or 0
                    except Exception:
                        total_patients = 0
                
                # Count today's appointments using created_at field
                from datetime import date
                today_appointments = Appointment.objects.filter(
                    hospital=selected_hospital_id,
                    appointment_date=date.today(),
                    status__in=['SCHEDULED', 'CONFIRMED']
                ).count()
                
                context.update({
                    'total_patients': total_patients,
                    'today_appointments': today_appointments,
                    'emergency_cases': 0,  # Will be implemented when emergency table exists
                    'pending_bills': Bill.objects.filter(
                        hospital_id=selected_hospital_id,
                        status='PENDING'
                    ).count(),
                    'revenue_today': Bill.objects.filter(
                        hospital_id=selected_hospital_id,
                        created_at__date=today,
                        status='PAID'
                    ).aggregate(total=Sum('total_amount'))['total'] or 0,
                    'revenue_month': Bill.objects.filter(
                        hospital_id=selected_hospital_id,
                        created_at__month=today.month,
                        status='PAID'
                    ).aggregate(total=Sum('total_amount'))['total'] or 0,
                    'total_staff': 25,  # Placeholder - will be implemented
                    'total_doctors': 8,  # Placeholder - will be implemented
                    'new_patients_today': Patient.objects.filter(registration_date=today).count(),
                    'pending_appointments': Appointment.objects.filter(
                        hospital=selected_hospital_id,
                        status='SCHEDULED'
                    ).count(),
                    # Recent pending items (actionable list)
                    'recent_pending_bills': Bill.objects.filter(hospital_id=selected_hospital_id, status='PENDING').order_by('-created_at'),
                    'recent_pending_appointments': Appointment.objects.filter(hospital=selected_hospital_id, status='SCHEDULED').order_by('-appointment_date'),
                    # Chart data placeholders (will be populated from cache below)
                    'revenue_chart': [],
                    'appointments_chart': [],
                    # Enabled modules for conditional quick-actions
                    'enabled_modules': hospital.get_enabled_modules() if hospital else [],
                    'recent_activities': [
                        {
                            'title': 'New patient registered',
                            'description': 'John Doe has been registered',
                            'timestamp': timezone.now() - timedelta(minutes=15),
                            'icon': 'person-plus'
                        },
                        {
                            'title': 'Appointment scheduled',
                            'description': 'Dr. Smith - 3:00 PM today',
                            'timestamp': timezone.now() - timedelta(minutes=30),
                            'icon': 'calendar-check'
                        },
                        {
                            'title': 'Bill payment received',
                            'description': 'Payment of $250 received',
                            'timestamp': timezone.now() - timedelta(minutes=45),
                            'icon': 'credit-card'
                        }
                    ]
                })
                
                # Cache and paginate: charts cached per-hospital for 5 minutes
                try:
                    rev_key = f'revenue_chart_{selected_hospital_id}'
                    appt_key = f'appointments_chart_{selected_hospital_id}'
                    revenue_chart = cache.get(rev_key)
                    if revenue_chart is None:
                        revenue_chart = [
                            Bill.objects.filter(
                                hospital_id=selected_hospital_id,
                                created_at__date=(today - timedelta(days=i)),
                                status='PAID'
                            ).aggregate(total=Sum('total_amount'))['total'] or 0
                            for i in reversed(range(7))
                        ]
                        cache.set(rev_key, revenue_chart, 300)
                    appointments_chart = cache.get(appt_key)
                    if appointments_chart is None:
                        appointments_chart = [
                            Appointment.objects.filter(hospital=selected_hospital_id, appointment_date=(today - timedelta(days=i))).count()
                            for i in reversed(range(7))
                        ]
                        cache.set(appt_key, appointments_chart, 300)
                    context['revenue_chart'] = revenue_chart
                    context['appointments_chart'] = appointments_chart

                    # Paginate recent pending lists (5 per page). Use separate query params.
                    page_bills = request.GET.get('page_pending', 1)
                    page_appts = request.GET.get('page_pending_appt', 1)
                    bills_qs = context.get('recent_pending_bills', Bill.objects.none())
                    appts_qs = context.get('recent_pending_appointments', Appointment.objects.none())
                    bills_paginator = Paginator(bills_qs, 5)
                    appts_paginator = Paginator(appts_qs, 5)
                    try:
                        bills_page = bills_paginator.page(page_bills)
                    except PageNotAnInteger:
                        bills_page = bills_paginator.page(1)
                    except EmptyPage:
                        bills_page = bills_paginator.page(bills_paginator.num_pages)

                    try:
                        appts_page = appts_paginator.page(page_appts)
                    except PageNotAnInteger:
                        appts_page = appts_paginator.page(1)
                    except EmptyPage:
                        appts_page = appts_paginator.page(appts_paginator.num_pages)

                    context['recent_pending_bills'] = bills_page
                    context['recent_pending_appointments'] = appts_page

                except Exception as e:
                    print(f"Hospital Admin Dashboard query error: {e}")
                    context.update({
                    'total_patients': 0,
                    'today_appointments': 0,
                    'emergency_cases': 0,
                    'pending_bills': 0,
                    'revenue_today': 0,
                    'revenue_month': 0,
                    'total_staff': 0,
                    'total_doctors': 0,
                    'new_patients_today': 0,
                    'pending_appointments': 0,
                    'recent_activities': []
                })
        
            except Exception as e:
                print(f"Hospital Admin Dashboard outer query error: {e}")
                context.update({
                    'total_patients': 0,
                    'today_appointments': 0,
                    'emergency_cases': 0,
                    'pending_bills': 0,
                    'revenue_today': 0,
                    'revenue_month': 0,
                    'total_staff': 0,
                    'total_doctors': 0,
                    'new_patients_today': 0,
                    'pending_appointments': 0,
                    'recent_activities': []
                })

        # Use hospital admin specific template
        return render(request, 'dashboard/hospital_admin_dashboard.html', context)
    
    elif user.role in ['ADMIN', 'SUPERADMIN']:
        # Admin Dashboard
        if selected_hospital_id:
            try:
                # Hospital-specific dashboard using correct database fields
                from django.db import connection

                # Prefer ORM count for portability and safety. Fall back to raw SQL only if ORM fails.
                try:
                    total_patients = Patient.objects.filter(hospital_id=selected_hospital_id, is_active=True).count()
                except Exception:
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute("SELECT COUNT(*) FROM patients_patient WHERE is_active = 1")
                            total_patients = cursor.fetchone()[0] or 0
                    except Exception:
                        total_patients = 0
                
                # Count today's appointments using created_at field
                from datetime import date
                today_appointments = Appointment.objects.filter(
                    hospital=selected_hospital_id,
                    appointment_date=date.today(),
                    status__in=['SCHEDULED', 'CONFIRMED']
                ).count()
                
                context.update({
                    'total_patients': total_patients,
                    'today_appointments': today_appointments,
                    'emergency_cases': 0,  # Will be implemented when emergency table exists
                    'pending_bills': Bill.objects.filter(
                        hospital_id=selected_hospital_id,
                        status='PENDING'
                    ).aggregate(total=Sum('total_amount'))['total'] or 0,
                    # Recent pending items
                    'recent_pending_bills': Bill.objects.filter(hospital_id=selected_hospital_id, status='PENDING').order_by('-created_at')[:5],
                    'recent_pending_appointments': Appointment.objects.filter(hospital=selected_hospital_id, status='SCHEDULED').order_by('-appointment_date')[:5],
                    # Charts
                    'revenue_chart': [
                        Bill.objects.filter(
                            hospital_id=selected_hospital_id,
                            created_at__date=(today - timedelta(days=i)),
                            status='PAID'
                        ).aggregate(total=Sum('total_amount'))['total'] or 0
                        for i in reversed(range(7))
                    ],
                    'appointments_chart': [
                        Appointment.objects.filter(hospital_id=selected_hospital_id, appointment_date=(today - timedelta(days=i))).count()
                        for i in reversed(range(7))
                    ],
                    'enabled_modules': hospital.get_enabled_modules() if hospital else [],
                    # Charts data (simplified for now)
                    'appointment_chart_data': [],
                    'revenue_chart_data': [],
                    'patient_chart_data': [],
                })
                
            except Exception as e:
                print(f"Dashboard query error: {e}")
                context.update({
                    'total_patients': 0,
                    'today_appointments': 0,
                    'emergency_cases': 0,
                    'pending_bills': 0,
                    'appointment_chart_data': [],
                    'revenue_chart_data': [],
                    'patient_chart_data': [],
                    'recent_appointments': [],  # Will be enabled once database schema is fixed
                    'recent_patients': [],  # Will be enabled once database schema is fixed
                })
        elif user.role == 'SUPERADMIN':
            # System-wide dashboard for SUPERADMIN
            context.update({
                'total_patients': 0,  # Temporarily disabled due to database column issues
                'today_appointments': 0,  # Temporarily disabled due to database column issues
                'emergency_cases': 0,  # Temporarily disabled due to table not existing
                'pending_bills': Bill.objects.filter(status='PENDING').aggregate(total=Sum('total_amount'))['total'] or 0,
                'appointment_chart_data': [],
                'revenue_chart_data': [],
                'patient_chart_data': [],
                'recent_appointments': [],  # Temporarily disabled due to database column issues
                'recent_patients': [],  # Temporarily disabled due to database column issues
                'show_hospital_selector': True,  # Show hospital selector in template
            })
        else:
            # Regular ADMIN without hospital selection - show basic dashboard
            try:
                total_patients = Patient.objects.count()
                today_appointments = Appointment.objects.filter(appointment_date=today).count()
                pending_bills = Bill.objects.filter(status='PENDING').count()
                pending_appointments = Appointment.objects.filter(status='SCHEDULED').count()
            except Exception as e:
                total_patients = 0
                today_appointments = 0
                pending_bills = 0
                pending_appointments = 0
            
            context.update({
                'total_patients': total_patients,
                'today_appointments': today_appointments,
                'emergency_cases': 0,  # Temporarily disabled due to table not existing
                'pending_bills': pending_bills,
                'total_staff': 0,
                'total_doctors': 0,
                'revenue_today': 0,
                'revenue_month': 0,
                'new_patients_today': 0,  # Temporarily simplified to avoid date field issues
                'pending_appointments': pending_appointments,
                'recent_activities': [],
                'hospital_selection_required': True,
            })
    
    elif user.role == 'DOCTOR':
        # Doctor Dashboard
        try:
            doctor_appointments = Appointment.objects.filter(doctor=user)
            my_appointments_today = doctor_appointments.filter(appointment_date=today).count()
            my_patients = doctor_appointments.values('patient').distinct().count()
            my_pending_appointments = doctor_appointments.filter(status='SCHEDULED').count()
            my_completed_appointments = doctor_appointments.filter(status='COMPLETED', appointment_date=today).count()
            upcoming_appointments = doctor_appointments.filter(
                appointment_date__gte=today,
                status='SCHEDULED'
            ).select_related('patient').order_by('appointment_date', 'appointment_time')[:5]
            
            context.update({
                'my_appointments_today': my_appointments_today,
                'my_patients': my_patients,
                'my_pending_appointments': my_pending_appointments,
                'my_completed_appointments': my_completed_appointments,
                'upcoming_appointments': upcoming_appointments,
            })
        except Exception as e:
            context.update({
                'my_appointments_today': 0,
                'my_patients': 0,
                'my_pending_appointments': 0,
                'my_completed_appointments': 0,
                'upcoming_appointments': [],
            })
        
    elif user.role == 'NURSE':
        # Nurse Dashboard
        context.update({
            'patients_assigned': 0,  # Would need to implement patient assignment
            'emergency_cases': 0,  # Temporarily disabled due to table not existing
            'vitals_recorded': 0,  # Would need to implement vitals tracking
        })
    
    elif user.role == 'RECEPTIONIST':
        # Receptionist Dashboard
        try:
            appointments_today = Appointment.objects.filter(appointment_date=today).count()
            waiting_patients = Appointment.objects.filter(
                appointment_date=today, 
                status='SCHEDULED'
            ).count()
        except Exception as e:
            appointments_today = 0
            waiting_patients = 0
            
        context.update({
            'appointments_today': appointments_today,
            'new_registrations': 0,  # Temporarily simplified to avoid date field issues
            'waiting_patients': waiting_patients,
        })
    
    # Add common context for all users
    try:
        from apps.core.models import ActivityLog
        context['recent_activities'] = ActivityLog.objects.order_by('-timestamp')[:10]
    except:
        context['recent_activities'] = []
    
    return render(request, 'dashboard/unified_dashboard.html', context)

def get_appointment_chart_data(hospital):
    """Get appointment data for the last 7 days - temporarily disabled"""
    # Temporarily returning empty data due to database column issues
    data = []
    for i in range(6, -1, -1):
        date = timezone.now().date() - timedelta(days=i)
        data.append({
            'date': date.strftime('%b %d'),
            'count': 0
        })
    return data

def get_revenue_chart_data(hospital):
    """Get revenue data for the last 7 days"""
    data = []
    for i in range(6, -1, -1):
        date = timezone.now().date() - timedelta(days=i)
        revenue = Bill.objects.filter(
            hospital=hospital,
            created_at__date=date,
            status='PAID'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        data.append({
            'date': date.strftime('%b %d'),
            'amount': float(revenue)
        })
    return data

def get_patient_chart_data(hospital):
    """Get patient registration data"""
    data = []
    for i in range(6, -1, -1):
        date = timezone.now().date() - timedelta(days=i)
        count = Patient.objects.filter(
            hospital=hospital,
            registration_date__date=date
        ).count()
        data.append({
            'date': date.strftime('%b %d'),
            'count': count
        })
    return data