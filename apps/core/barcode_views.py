# apps/core/barcode_views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json

from .utils.barcode_generator import BarcodeScanner, DocumentBarcodeGenerator
from apps.patients.models import Patient
from apps.doctors.models import Doctor
from apps.appointments.models import Appointment
from apps.laboratory.models import LabOrder
from apps.radiology.models import RadiologyOrder
from apps.billing.models import Invoice

@method_decorator(login_required, name='dispatch')
class BarcodeScannerView(View):
    """Hospital barcode scanner interface"""
    
    def get(self, request):
        return render(request, 'core/barcode_scanner.html')

@login_required
@require_http_methods(["POST"])
def barcode_search(request):
    """Search hospital records by barcode data"""
    try:
        data = json.loads(request.body)
        barcode_data = data.get('barcode_data', '').strip()
        
        if not barcode_data:
            return JsonResponse({
                'success': False,
                'error': 'No barcode data provided'
            })
        
        # Use the barcode scanner to search records
        results = BarcodeScanner.search_by_barcode(barcode_data)
        
        if results:
            return JsonResponse({
                'success': True,
                'results': results,
                'barcode_data': barcode_data
            })
        else:
            return JsonResponse({
                'success': False,
                'results': [],
                'error': 'No records found for this barcode'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Search failed: {str(e)}'
        })

@login_required
@require_http_methods(["POST"])
def manual_search(request):
    """Manual search when barcode scanning fails"""
    try:
        data = json.loads(request.body)
        query = data.get('query', '').strip()
        
        if not query:
            return JsonResponse({
                'success': False,
                'error': 'No search query provided'
            })
        
        results = []
        
        # Search patients
        patients = Patient.objects.filter(
            user__first_name__icontains=query
        ) or Patient.objects.filter(
            user__last_name__icontains=query
        ) or Patient.objects.filter(
            phone__icontains=query
        ) or Patient.objects.filter(
            patient_id__icontains=query
        )
        
        for patient in patients[:3]:
            results.append({
                'type': 'patient',
                'title': f"Patient - {patient.user.get_full_name()}",
                'subtitle': f"ID: {patient.patient_id} - Phone: {patient.phone}",
                'url': f'/patients/{patient.id}/'
            })
        
        # Search doctors
        doctors = Doctor.objects.filter(
            user__first_name__icontains=query
        ) or Doctor.objects.filter(
            user__last_name__icontains=query
        ) or Doctor.objects.filter(
            employee_id__icontains=query
        )
        
        for doctor in doctors[:3]:
            results.append({
                'type': 'doctor',
                'title': f"Dr. {doctor.user.get_full_name()}",
                'subtitle': f"ID: {doctor.employee_id} - {doctor.specialization}",
                'url': f'/doctors/{doctor.id}/'
            })
        
        # Search appointments
        appointments = Appointment.objects.filter(
            patient__user__first_name__icontains=query
        ) or Appointment.objects.filter(
            patient__user__last_name__icontains=query
        ) or Appointment.objects.filter(
            serial_number__icontains=query
        )
        
        for apt in appointments[:3]:
            results.append({
                'type': 'appointment',
                'title': f"Appointment - {apt.patient.user.get_full_name()}",
                'subtitle': f"Dr. {apt.doctor.user.get_full_name()} - {apt.appointment_date}",
                'url': f'/appointments/{apt.id}/'
            })
        
        return JsonResponse({
            'success': True,
            'results': results,
            'query': query
        })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Search failed: {str(e)}'
        })

@login_required
@require_http_methods(["POST"])
def generate_barcode(request):
    """Generate barcode for hospital objects"""
    try:
        data = json.loads(request.body)
        object_id = data.get('object_id')
        object_type = data.get('object_type', '').lower()
        
        if not object_id or not object_type:
            return JsonResponse({
                'success': False,
                'error': 'Object ID and type are required'
            })
        
        generator = DocumentBarcodeGenerator()
        barcode_data = None
        serial_number = None
        
        try:
            if object_type == 'patient':
                patient = Patient.objects.get(id=object_id)
                barcode_data = generator.generate_patient_barcode(patient)
                serial_number = getattr(patient, 'serial_number', None)
                
            elif object_type == 'doctor':
                doctor = Doctor.objects.get(id=object_id)
                barcode_data = generator.generate_doctor_barcode(doctor)
                serial_number = getattr(doctor, 'serial_number', None)
                
            elif object_type == 'appointment':
                appointment = Appointment.objects.get(id=object_id)
                barcode_data = generator.generate_appointment_barcode(appointment)
                serial_number = getattr(appointment, 'serial_number', None)
                
            elif object_type == 'laborder':
                lab_order = LabOrder.objects.get(id=object_id)
                barcode_data = generator.generate_lab_order_barcode(lab_order)
                serial_number = getattr(lab_order, 'serial_number', None)
                
            elif object_type == 'radiologyorder':
                radiology_order = RadiologyOrder.objects.get(id=object_id)
                barcode_data = generator.generate_radiology_order_barcode(radiology_order)
                serial_number = getattr(radiology_order, 'serial_number', None)
                
            elif object_type == 'invoice':
                invoice = Invoice.objects.get(id=object_id)
                barcode_data = generator.generate_invoice_barcode(invoice)
                serial_number = getattr(invoice, 'serial_number', None)
                
            else:
                return JsonResponse({
                    'success': False,
                    'error': f'Unsupported object type: {object_type}'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Object not found: {str(e)}'
            })
        
        if barcode_data:
            return JsonResponse({
                'success': True,
                'barcode_data': barcode_data,
                'serial_number': serial_number,
                'object_type': object_type
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Failed to generate barcode'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Barcode generation failed: {str(e)}'
        })
