# ipd/views.py
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.core.mixins import UnifiedSystemMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q
from .models import IPDRecord
from .forms import IPDRecordForm

class IPDListView(LoginRequiredMixin, ListView):
    model = IPDRecord
    template_name = 'ipd/ipd_list_clean.html'  # Use the clean template instead
    context_object_name = 'ipd_records'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        # Fix pagination warning by adding proper ordering
        return queryset.select_related('patient', 'attending_doctor', 'referring_doctor', 'room', 'bed').order_by('-admission_date')

class IPDCreateView(UnifiedSystemMixin, LoginRequiredMixin, CreateView):
    model = IPDRecord
    form_class = IPDRecordForm
    template_name = 'ipd/ipd_form.html'
    success_url = reverse_lazy('ipd:ipd_list')

class IPDDetailView(LoginRequiredMixin, DetailView):
    model = IPDRecord
    template_name = 'ipd/ipd_detail.html'
    context_object_name = 'ipd_record'

class IPDUpdateView(LoginRequiredMixin, UpdateView):
    model = IPDRecord
    form_class = IPDRecordForm
    template_name = 'ipd/ipd_form.html'
    success_url = reverse_lazy('ipd:ipd_list')

class IPDDeleteView(LoginRequiredMixin, DeleteView):
    model = IPDRecord
    template_name = 'ipd/ipd_confirm_delete.html'
    success_url = reverse_lazy('ipd:ipd_list')


def ajax_search_patients(request):
    """AJAX view to search patients for IPD form"""
    if not request.user.is_authenticated:
        return JsonResponse({'results': []})
    
    term = request.GET.get('term', '').strip()
    page = int(request.GET.get('page', 1))
    page_size = 20
    
    if len(term) < 2:
        return JsonResponse({'results': []})
    
    try:
        from apps.patients.models import Patient
        
        # Search patients by name, patient_id, or phone
        patients = Patient.objects.filter(
            Q(first_name__icontains=term) |
            Q(last_name__icontains=term) |
            Q(patient_id__icontains=term) |
            Q(phone__icontains=term) |
            Q(email__icontains=term)
        ).distinct()[:page_size]
        
        results = []
        for patient in patients:
            full_name = patient.get_full_name() if hasattr(patient, 'get_full_name') else f"{patient.first_name} {patient.last_name}".strip()
            patient_display = f"{full_name}"
            if hasattr(patient, 'patient_id') and patient.patient_id:
                patient_display += f" (ID: {patient.patient_id})"
            if hasattr(patient, 'phone') and patient.phone:
                patient_display += f" - {patient.phone}"
                
            results.append({
                'id': patient.id,
                'text': patient_display,
                'full_name': full_name,
                'patient_id': getattr(patient, 'patient_id', 'N/A'),
                'phone': getattr(patient, 'phone', 'N/A')
            })
        
        return JsonResponse({
            'results': results,
            'pagination': {'more': len(results) == page_size}
        })
        
    except ImportError:
        # Fallback if patients app not available
        return JsonResponse({'results': []})


def ajax_search_doctors(request):
    """AJAX view to search doctors for IPD form"""
    if not request.user.is_authenticated:
        return JsonResponse({'results': []})
    
    term = request.GET.get('term', '').strip()
    page = int(request.GET.get('page', 1))
    page_size = 20
    
    if len(term) < 2:
        return JsonResponse({'results': []})
    
    try:
        from apps.doctors.models import Doctor
        
        # Search doctors by name, doctor ID, or specialization
        doctors = Doctor.objects.filter(
            Q(user__first_name__icontains=term) |
            Q(user__last_name__icontains=term) |
            Q(user__username__icontains=term) |
            Q(specialization__icontains=term) |
            Q(license_number__icontains=term)
        ).distinct()[:page_size]
        
        results = []
        for doctor in doctors:
            full_name = doctor.user.get_full_name() if hasattr(doctor.user, 'get_full_name') else f"{doctor.user.first_name} {doctor.user.last_name}".strip()
            doctor_display = f"Dr. {full_name}"
            
            if hasattr(doctor, 'specialization') and doctor.specialization:
                doctor_display += f" ({doctor.specialization})"
            if hasattr(doctor, 'license_number') and doctor.license_number:
                doctor_display += f" - Lic: {doctor.license_number}"
                
            results.append({
                'id': doctor.id,
                'text': doctor_display,
                'full_name': full_name,
                'specialization': getattr(doctor, 'specialization', 'General'),
                'license_number': getattr(doctor, 'license_number', 'N/A')
            })
        
        return JsonResponse({
            'results': results,
            'pagination': {'more': len(results) == page_size}
        })
        
    except ImportError:
        # Fallback - try to get from staff/users with doctor role
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            doctors = User.objects.filter(
                Q(first_name__icontains=term) |
                Q(last_name__icontains=term) |
                Q(username__icontains=term),
                role__in=['DOCTOR', 'SURGEON', 'SPECIALIST']
            )[:page_size]
            
            results = []
            for doctor in doctors:
                full_name = doctor.get_full_name() if hasattr(doctor, 'get_full_name') else f"{doctor.first_name} {doctor.last_name}".strip()
                results.append({
                    'id': doctor.id,
                    'text': f"Dr. {full_name}",
                    'full_name': full_name,
                    'specialization': getattr(doctor, 'role', 'Doctor')
                })
            
            return JsonResponse({
                'results': results,
                'pagination': {'more': len(results) == page_size}
            })
            
        except Exception:
            return JsonResponse({'results': []})


def ajax_get_available_beds(request):
    """AJAX view to get available beds for selected room"""
    if not request.user.is_authenticated:
        return JsonResponse({'results': []})
    
    room_id = request.GET.get('room_id')
    if not room_id:
        return JsonResponse({'results': []})
    
    try:
        from .models import Bed
        
        # Get available beds for the selected room
        beds = Bed.objects.filter(
            room_id=room_id,
            available=True
        ).order_by('number')
        
        results = []
        for bed in beds:
            results.append({
                'id': bed.id,
                'text': f"Bed {bed.number}",
                'number': bed.number
            })
        
        return JsonResponse({'results': results})
        
    except Exception as e:
        return JsonResponse({'results': [], 'error': str(e)})
