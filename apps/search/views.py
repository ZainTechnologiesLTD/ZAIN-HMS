from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.urls import reverse

from apps.patients.models import Patient
from apps.doctors.models import Doctor
from apps.appointments.models import Appointment
from apps.laboratory.models import LabTest, LabOrder
from apps.pharmacy.models import Medicine
from apps.radiology.models import RadiologyTest, RadiologyOrder


@login_required
def global_search_api(request):
    """API endpoint for global search with type filtering"""
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'all')
    
    if not query or len(query) < 2:
        return JsonResponse({'results': []})
    
    results = []
    
    # Patients
    if search_type in ['all', 'patients']:
        patients = Patient.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(patient_id__icontains=query) |
            Q(phone__icontains=query) |
            Q(email__icontains=query)
        )[:10]
        
        for patient in patients:
            results.append({
                'type': 'patient',
                'id': patient.id,
                'title': patient.get_full_name(),
                'subtitle': f"ID: {patient.patient_id} | Phone: {patient.phone or 'N/A'}",
                'url': reverse('patients:detail', args=[patient.id]),
                'icon': 'fas fa-user-injured'
            })
    
    # Doctors
    if search_type in ['all', 'doctors']:
        doctors = Doctor.objects.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(doctor_id__icontains=query) |
            Q(specialization__icontains=query) |
            Q(user__email__icontains=query)
        ).select_related('user')[:10]
        
        for doctor in doctors:
            results.append({
                'type': 'doctor',
                'id': doctor.id,
                'title': doctor.get_full_name(),
                'subtitle': f"ID: {doctor.doctor_id} | {doctor.specialization}",
                'url': reverse('doctors:detail', args=[doctor.id]),
                'icon': 'fas fa-user-md'
            })
    
    # Appointments
    if search_type in ['all', 'appointments']:
        appointments = Appointment.objects.filter(
            Q(patient__first_name__icontains=query) |
            Q(patient__last_name__icontains=query) |
            Q(doctor__user__first_name__icontains=query) |
            Q(doctor__user__last_name__icontains=query) |
            Q(appointment_number__icontains=query)
        ).select_related('patient', 'doctor__user')[:10]
        
        for appointment in appointments:
            results.append({
                'type': 'appointment',
                'id': appointment.id,
                'title': f"Appointment #{appointment.appointment_number}",
                'subtitle': f"{appointment.patient.get_full_name()} with Dr. {appointment.doctor.get_full_name()} on {appointment.appointment_date}",
                'url': reverse('appointments:detail', args=[appointment.id]),
                'icon': 'fas fa-calendar-check'
            })
    
    # Lab Tests
    if search_type in ['all', 'lab_tests']:
        lab_tests = LabTest.objects.filter(
            Q(name__icontains=query) |
            Q(test_code__icontains=query) |
            Q(category__name__icontains=query)
        ).select_related('category')[:10]
        
        for test in lab_tests:
            results.append({
                'type': 'lab_test',
                'id': test.id,
                'title': test.name,
                'subtitle': f"Code: {test.test_code} | Category: {test.category.name} | Price: ${test.price}",
                'url': f"/laboratory/tests/{test.id}/",
                'icon': 'fas fa-vial'
            })
    
    # Medicines
    if search_type in ['all', 'medicines']:
        medicines = Medicine.objects.filter(
            Q(generic_name__icontains=query) |
            Q(brand_name__icontains=query) |
            Q(medicine_code__icontains=query)
        )[:10]
        
        for medicine in medicines:
            results.append({
                'type': 'medicine',
                'id': medicine.id,
                'title': f"{medicine.generic_name} - {medicine.brand_name}",
                'subtitle': f"Code: {medicine.medicine_code} | Strength: {medicine.strength} | Price: ${medicine.price}",
                'url': f"/pharmacy/medicines/{medicine.id}/",
                'icon': 'fas fa-pills'
            })
    
    # Lab Orders
    if search_type in ['all', 'lab_orders']:
        lab_orders = LabOrder.objects.filter(
            Q(order_number__icontains=query) |
            Q(patient__first_name__icontains=query) |
            Q(patient__last_name__icontains=query)
        ).select_related('patient', 'doctor__user')[:10]
        
        for order in lab_orders:
            results.append({
                'type': 'lab_order',
                'id': order.id,
                'title': f"Lab Order #{order.order_number}",
                'subtitle': f"{order.patient.get_full_name()} | Status: {order.get_status_display()}",
                'url': f"/laboratory/orders/{order.id}/",
                'icon': 'fas fa-flask'
            })
    
    # Radiology Tests (if exists)
    try:
        if search_type in ['all', 'radiology_tests']:
            from apps.radiology.models import RadiologyTest
            radiology_tests = RadiologyTest.objects.filter(
                Q(name__icontains=query) |
                Q(test_code__icontains=query)
            )[:10]
            
            for test in radiology_tests:
                results.append({
                    'type': 'radiology_test',
                    'id': test.id,
                    'title': test.name,
                    'subtitle': f"Code: {test.test_code} | Price: ${test.price}",
                    'url': f"/radiology/tests/{test.id}/",
                    'icon': 'fas fa-x-ray'
                })
    except ImportError:
        pass
    
    # Sort results by relevance (exact matches first)
    def sort_key(item):
        title_lower = item['title'].lower()
        query_lower = query.lower()
        
        if query_lower in title_lower:
            if title_lower.startswith(query_lower):
                return 0  # Starts with query
            else:
                return 1  # Contains query
        return 2  # Subtitle match
    
    results.sort(key=sort_key)
    
    return JsonResponse({
        'results': results[:50],  # Limit to 50 results
        'total': len(results)
    })


@login_required
def search_page(request):
    """Full search page with filters and pagination"""
    query = request.GET.get('q', '')
    search_type = request.GET.get('type', 'all')
    
    context = {
        'query': query,
        'search_type': search_type,
        'search_types': [
            ('all', 'All'),
            ('patients', 'Patients'),
            ('doctors', 'Doctors'),
            ('appointments', 'Appointments'),
            ('lab_tests', 'Lab Tests'),
            ('medicines', 'Medicines'),
            ('lab_orders', 'Lab Orders'),
        ]
    }
    
    if query and len(query) >= 2:
        # Perform search based on type
        results = []
        
        if search_type == 'all' or search_type == 'patients':
            patients = Patient.objects.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(patient_id__icontains=query) |
                Q(phone__icontains=query)
            )
            results.extend([('patient', p) for p in patients])
        
        if search_type == 'all' or search_type == 'doctors':
            doctors = Doctor.objects.filter(
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query) |
                Q(specialization__icontains=query)
            ).select_related('user')
            results.extend([('doctor', d) for d in doctors])
        
        # Add pagination
        paginator = Paginator(results, 20)
        page_number = request.GET.get('page')
        page_results = paginator.get_page(page_number)
        
        context['results'] = page_results
        context['total_results'] = len(results)
    
    return render(request, 'search/search_page.html', context)


@login_required
def quick_search_suggestions(request):
    """Quick search suggestions for autocomplete"""
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 1:
        return JsonResponse({'suggestions': []})
    
    suggestions = []
    
    # Patient suggestions
    patients = Patient.objects.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(patient_id__icontains=query)
    )[:5]
    
    for patient in patients:
        suggestions.append({
            'text': patient.get_full_name(),
            'type': 'patient',
            'url': reverse('patients:detail', args=[patient.id])
        })
    
    # Doctor suggestions
    doctors = Doctor.objects.filter(
        Q(user__first_name__icontains=query) |
        Q(user__last_name__icontains=query) |
        Q(specialization__icontains=query)
    ).select_related('user')[:5]
    
    for doctor in doctors:
        suggestions.append({
            'text': f"Dr. {doctor.get_full_name()}",
            'type': 'doctor',
            'url': reverse('doctors:detail', args=[doctor.id])
        })
    
    return JsonResponse({'suggestions': suggestions})
