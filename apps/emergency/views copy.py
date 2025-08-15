from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime, timedelta

from .models import (
    EmergencyCase, EmergencyTriage, EmergencyTreatment,
    EmergencyVitalSigns, EmergencyMedication, EmergencyDiagnosticTest,
    EmergencyTransfer
)
from .forms import (
    EmergencyCaseForm, EmergencyTriageForm, EmergencyTreatmentForm,
    EmergencyVitalSignsForm, EmergencyMedicationForm, 
    EmergencyDiagnosticTestForm, EmergencyTransferForm
)
from apps.patients.models import Patient
from apps.doctors.models import Doctor


@login_required
def emergency_dashboard(request):
    """Emergency department dashboard"""
    # Get statistics
    total_cases = EmergencyCase.objects.count()
    active_cases = EmergencyCase.objects.filter(status__in=['WAITING', 'IN_TREATMENT']).count()
    critical_cases = EmergencyCase.objects.filter(
        priority='CRITICAL', 
        status__in=['WAITING', 'IN_TREATMENT']
    ).count()
    
    # Recent cases
    recent_cases = EmergencyCase.objects.select_related('patient').order_by('-arrival_time')[:10]
    
    # Waiting patients by priority
    waiting_by_priority = EmergencyCase.objects.filter(status='WAITING').values('priority').annotate(count=Count('id'))
    
    # Cases by status
    cases_by_status = EmergencyCase.objects.values('status').annotate(count=Count('id'))
    
    context = {
        'total_cases': total_cases,
        'active_cases': active_cases,
        'critical_cases': critical_cases,
        'recent_cases': recent_cases,
        'waiting_by_priority': waiting_by_priority,
        'cases_by_status': cases_by_status,
    }
    return render(request, 'emergency/dashboard.html', context)


@login_required
def emergency_case_list(request):
    """List all emergency cases"""
    cases = EmergencyCase.objects.select_related('patient').order_by('-arrival_time')
    
    # Filters
    status_filter = request.GET.get('status')
    priority_filter = request.GET.get('priority')
    date_filter = request.GET.get('date')
    search = request.GET.get('search')
    
    if status_filter:
        cases = cases.filter(status=status_filter)
    if priority_filter:
        cases = cases.filter(priority=priority_filter)
    if date_filter:
        cases = cases.filter(arrival_time__date=date_filter)
    if search:
        cases = cases.filter(
            Q(case_number__icontains=search) |
            Q(patient__first_name__icontains=search) |
            Q(patient__last_name__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(cases, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_choices': EmergencyCase.STATUS_CHOICES,
        'priority_choices': EmergencyCase.PRIORITY_CHOICES,
        'current_filters': {
            'status': status_filter,
            'priority': priority_filter,
            'date': date_filter,
            'search': search,
        }
    }
    return render(request, 'emergency/case_list.html', context)


@login_required
def emergency_case_detail(request, case_id):
    """Emergency case detail view"""
    case = get_object_or_404(EmergencyCase.objects.select_related('patient'), id=case_id)
    
    # Related data
    triage = case.triage_records.first()
    treatments = case.treatments.all().order_by('-treatment_time')
    vital_signs = case.vital_signs.all().order_by('-recorded_time')[:5]
    medications = case.medications.all().order_by('-administered_time')
    diagnostic_tests = case.diagnostic_tests.all().order_by('-ordered_time')
    transfers = case.transfers.all().order_by('-transfer_time')
    
    context = {
        'case': case,
        'triage': triage,
        'treatments': treatments,
        'vital_signs': vital_signs,
        'medications': medications,
        'diagnostic_tests': diagnostic_tests,
        'transfers': transfers,
    }
    return render(request, 'emergency/case_detail.html', context)


@login_required
def emergency_case_add(request):
    """Add new emergency case"""
    if request.method == 'POST':
        form = EmergencyCaseForm(request.POST)
        if form.is_valid():
            case = form.save()
            messages.success(request, f'Emergency case {case.case_number} created successfully.')
            return redirect('emergency:case_detail', case_id=case.id)
    else:
        form = EmergencyCaseForm()
    
    return render(request, 'emergency/case_form.html', {
        'form': form,
        'title': 'Add Emergency Case'
    })


@login_required
def emergency_case_edit(request, case_id):
    """Edit emergency case"""
    case = get_object_or_404(EmergencyCase, id=case_id)
    
    if request.method == 'POST':
        form = EmergencyCaseForm(request.POST, instance=case)
        if form.is_valid():
            form.save()
            messages.success(request, 'Emergency case updated successfully.')
            return redirect('emergency:case_detail', case_id=case.id)
    else:
        form = EmergencyCaseForm(instance=case)
    
    return render(request, 'emergency/case_form.html', {
        'form': form,
        'case': case,
        'title': 'Edit Emergency Case'
    })


@login_required
@require_POST
def update_case_status(request, case_id):
    """Update emergency case status via AJAX"""
    case = get_object_or_404(EmergencyCase, id=case_id)
    new_status = request.POST.get('status')
    
    if new_status in dict(EmergencyCase.STATUS_CHOICES):
        case.status = new_status
        if new_status == 'DISCHARGED':
            case.discharge_time = timezone.now()
        case.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Status updated successfully',
            'new_status': case.get_status_display()
        })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid status'
    })


@login_required
def triage_add(request, case_id):
    """Add triage assessment"""
    case = get_object_or_404(EmergencyCase, id=case_id)
    
    if request.method == 'POST':
        form = EmergencyTriageForm(request.POST)
        if form.is_valid():
            triage = form.save(commit=False)
            triage.case = case
            triage.triage_nurse = request.user
            triage.save()
            
            # Update case priority based on triage
            case.priority = triage.priority_assigned
            case.save()
            
            messages.success(request, 'Triage assessment added successfully.')
            return redirect('emergency:case_detail', case_id=case.id)
    else:
        form = EmergencyTriageForm()
    
    return render(request, 'emergency/triage_form.html', {
        'form': form,
        'case': case,
        'title': 'Add Triage Assessment'
    })


@login_required
def treatment_add(request, case_id):
    """Add treatment record"""
    case = get_object_or_404(EmergencyCase, id=case_id)
    
    if request.method == 'POST':
        form = EmergencyTreatmentForm(request.POST)
        if form.is_valid():
            treatment = form.save(commit=False)
            treatment.case = case
            treatment.save()
            
            # Update case status to in treatment
            if case.status == 'WAITING':
                case.status = 'IN_TREATMENT'
                case.save()
            
            messages.success(request, 'Treatment record added successfully.')
            return redirect('emergency:case_detail', case_id=case.id)
    else:
        form = EmergencyTreatmentForm()
    
    return render(request, 'emergency/treatment_form.html', {
        'form': form,
        'case': case,
        'title': 'Add Treatment'
    })


@login_required
def vital_signs_add(request, case_id):
    """Add vital signs"""
    case = get_object_or_404(EmergencyCase, id=case_id)
    
    if request.method == 'POST':
        form = EmergencyVitalSignsForm(request.POST)
        if form.is_valid():
            vital_signs = form.save(commit=False)
            vital_signs.case = case
            vital_signs.recorded_by = request.user
            vital_signs.save()
            
            messages.success(request, 'Vital signs recorded successfully.')
            return redirect('emergency:case_detail', case_id=case.id)
    else:
        form = EmergencyVitalSignsForm()
    
    return render(request, 'emergency/vital_signs_form.html', {
        'form': form,
        'case': case,
        'title': 'Record Vital Signs'
    })


@login_required
def medication_add(request, case_id):
    """Add medication"""
    case = get_object_or_404(EmergencyCase, id=case_id)
    
    if request.method == 'POST':
        form = EmergencyMedicationForm(request.POST)
        if form.is_valid():
            medication = form.save(commit=False)
            medication.case = case
            medication.save()
            
            messages.success(request, 'Medication order added successfully.')
            return redirect('emergency:case_detail', case_id=case.id)
    else:
        form = EmergencyMedicationForm()
    
    return render(request, 'emergency/medication_form.html', {
        'form': form,
        'case': case,
        'title': 'Add Medication'
    })


@login_required
@require_POST
def medication_administer(request, medication_id):
    """Mark medication as administered"""
    medication = get_object_or_404(EmergencyMedication, id=medication_id)
    medication.status = 'ADMINISTERED'
    medication.administered_time = timezone.now()
    medication.administered_by = request.user
    medication.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Medication marked as administered'
    })


@login_required
def diagnostic_test_add(request, case_id):
    """Add diagnostic test order"""
    case = get_object_or_404(EmergencyCase, id=case_id)
    
    if request.method == 'POST':
        form = EmergencyDiagnosticTestForm(request.POST, request.FILES)
        if form.is_valid():
            test = form.save(commit=False)
            test.case = case
            test.save()
            
            messages.success(request, 'Diagnostic test ordered successfully.')
            return redirect('emergency:case_detail', case_id=case.id)
    else:
        form = EmergencyDiagnosticTestForm()
    
    return render(request, 'emergency/diagnostic_test_form.html', {
        'form': form,
        'case': case,
        'title': 'Order Diagnostic Test'
    })


@login_required
def transfer_add(request, case_id):
    """Add transfer record"""
    case = get_object_or_404(EmergencyCase, id=case_id)
    
    if request.method == 'POST':
        form = EmergencyTransferForm(request.POST)
        if form.is_valid():
            transfer = form.save(commit=False)
            transfer.case = case
            transfer.transferred_by = request.user
            transfer.save()
            
            # Update case status
            case.status = 'TRANSFERRED'
            case.save()
            
            messages.success(request, 'Transfer record added successfully.')
            return redirect('emergency:case_detail', case_id=case.id)
    else:
        form = EmergencyTransferForm()
    
    return render(request, 'emergency/transfer_form.html', {
        'form': form,
        'case': case,
        'title': 'Transfer Patient'
    })


@login_required
def waiting_list(request):
    """Waiting patients list"""
    waiting_cases = EmergencyCase.objects.filter(
        status='WAITING'
    ).select_related('patient').order_by('priority', 'arrival_time')
    
    return render(request, 'emergency/waiting_list.html', {
        'waiting_cases': waiting_cases
    })


@login_required
def active_cases(request):
    """Active cases list"""
    active_cases = EmergencyCase.objects.filter(
        status__in=['WAITING', 'IN_TREATMENT']
    ).select_related('patient').order_by('priority', 'arrival_time')
    
    return render(request, 'emergency/active_cases.html', {
        'active_cases': active_cases
    })


@login_required
def search_patient(request):
    """Search patient for emergency registration"""
    query = request.GET.get('q', '')
    
    if query:
        patients = Patient.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(patient_id__icontains=query) |
            Q(phone__icontains=query)
        )[:10]
        
        patient_data = [{
            'id': p.id,
            'name': f"{p.first_name} {p.last_name}",
            'patient_id': p.patient_id,
            'phone': p.phone,
            'age': p.age if hasattr(p, 'age') else 'N/A'
        } for p in patients]
        
        return JsonResponse({'patients': patient_data})
    
    return JsonResponse({'patients': []})


@login_required
def emergency_reports(request):
    """Emergency department reports"""
    today = timezone.now().date()
    last_week = today - timedelta(days=7)
    last_month = today - timedelta(days=30)
    
    # Today's statistics
    today_cases = EmergencyCase.objects.filter(arrival_time__date=today).count()
    today_discharges = EmergencyCase.objects.filter(discharge_time__date=today).count()
    
    # Weekly statistics
    weekly_cases = EmergencyCase.objects.filter(arrival_time__date__gte=last_week).count()
    
    # Monthly statistics
    monthly_cases = EmergencyCase.objects.filter(arrival_time__date__gte=last_month).count()
    
    # Cases by priority (last 30 days)
    priority_stats = EmergencyCase.objects.filter(
        arrival_time__date__gte=last_month
    ).values('priority').annotate(count=Count('id'))
    
    # Average waiting time (last 7 days)
    recent_cases = EmergencyCase.objects.filter(
        arrival_time__date__gte=last_week,
        status__in=['DISCHARGED', 'TRANSFERRED']
    )
    
    context = {
        'today_cases': today_cases,
        'today_discharges': today_discharges,
        'weekly_cases': weekly_cases,
        'monthly_cases': monthly_cases,
        'priority_stats': priority_stats,
        'recent_cases': recent_cases,
    }
    
    return render(request, 'emergency/reports.html', context)


@login_required
def print_case(request, case_id):
    """Print emergency case details"""
    case = get_object_or_404(EmergencyCase.objects.select_related('patient'), id=case_id)
    
    # Get all related data
    triage = case.triage_records.first()
    treatments = case.treatments.all().order_by('-treatment_time')
    vital_signs = case.vital_signs.all().order_by('-recorded_time')
    medications = case.medications.all().order_by('-administered_time')
    diagnostic_tests = case.diagnostic_tests.all().order_by('-ordered_time')
    
    context = {
        'case': case,
        'triage': triage,
        'treatments': treatments,
        'vital_signs': vital_signs,
        'medications': medications,
        'diagnostic_tests': diagnostic_tests,
    }
    
    return render(request, 'emergency/print_case.html', context)


# AJAX Views for real-time updates
@login_required
def get_case_status(request, case_id):
    """Get current case status (AJAX)"""
    case = get_object_or_404(EmergencyCase, id=case_id)
    return JsonResponse({
        'status': case.status,
        'status_display': case.get_status_display(),
        'priority': case.priority,
        'priority_display': case.get_priority_display()
    })


@login_required
def get_waiting_count(request):
    """Get current waiting patient count (AJAX)"""
    count = EmergencyCase.objects.filter(status='WAITING').count()
    critical_count = EmergencyCase.objects.filter(
        status='WAITING', 
        priority='CRITICAL'
    ).count()
    
    return JsonResponse({
        'waiting_count': count,
        'critical_count': critical_count
    })