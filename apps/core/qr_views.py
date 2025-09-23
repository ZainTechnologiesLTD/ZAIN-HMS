# apps/core/qr_views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.db.models import Q
from django.utils.translation import gettext as _
from apps.core.utils.qr_code import qr_generator
from apps.patients.models import Patient
from apps.doctors.models import Doctor
from apps.appointments.models import Appointment
from apps.laboratory.models import LabOrder
from apps.radiology.models import RadiologyOrder
from apps.billing.models import Invoice
import json
import logging

logger = logging.getLogger(__name__)

@method_decorator(login_required, name='dispatch')
class QRScannerView(View):
    """QR Code scanner interface"""
    
    def get(self, request):
        """Display QR scanner page"""
        return render(request, 'core/qr_scanner.html')

@method_decorator(login_required, name='dispatch')
class QRSearchView(View):
    """Search records using QR code data or manual search"""
    
    def post(self, request):
        """Process QR code data or search query"""
        try:
            data = json.loads(request.body)
            qr_data = data.get('qr_data', '')
            search_query = data.get('search_query', '')
            
            results = []
            
            if qr_data:
                # Try to decrypt QR code data
                decrypted_data = qr_generator.decrypt_data(qr_data)
                if decrypted_data:
                    results = self._search_by_qr_data(decrypted_data)
                else:
                    # Fallback: treat as plain text search
                    results = self._search_by_text(qr_data)
            elif search_query:
                results = self._search_by_text(search_query)
            
            return JsonResponse({
                'success': True,
                'results': results,
                'count': len(results)
            })
            
        except Exception as e:
            logger.error(f"QR search error: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    def _search_by_qr_data(self, qr_data):
        """Search using decrypted QR code data"""
        results = []
        
        try:
            record_type = qr_data.get('type')
            record_id = qr_data.get('id')
            
            if record_type == 'patient':
                patient = Patient.objects.get(id=record_id)
                results.append({
                    'type': 'patient',
                    'id': str(patient.id),
                    'title': patient.get_full_name(),
                    'subtitle': f"ID: {patient.patient_id}",
                    'details': {
                        'phone': patient.phone,
                        'email': patient.email,
                        'blood_group': patient.blood_group,
                    },
                    'url': f'/patients/{patient.id}/'
                })
            
            elif record_type == 'doctor':
                doctor = Doctor.objects.get(id=record_id)
                results.append({
                    'type': 'doctor',
                    'id': str(doctor.id),
                    'title': doctor.get_full_name(),
                    'subtitle': str(doctor.specialization) if doctor.specialization else '',
                    'details': {
                        'department': str(doctor.department) if doctor.department else '',
                        'phone': doctor.phone,
                        'email': doctor.email,
                    },
                    'url': f'/doctors/{doctor.id}/'
                })
            
            elif record_type == 'appointment':
                appointment = Appointment.objects.get(id=record_id)
                results.append({
                    'type': 'appointment',
                    'id': str(appointment.id),
                    'title': f"Appointment {appointment.appointment_number}",
                    'subtitle': f"{appointment.patient.get_full_name()} - {appointment.doctor.get_full_name()}",
                    'details': {
                        'date': appointment.appointment_date.isoformat() if appointment.appointment_date else None,
                        'time': appointment.appointment_time.isoformat() if appointment.appointment_time else None,
                        'status': appointment.status,
                        'serial': appointment.serial_number,
                    },
                    'url': f'/appointments/{appointment.id}/'
                })
            
            elif record_type == 'lab_order':
                lab_order = LabOrder.objects.get(id=record_id)
                results.append({
                    'type': 'lab_order',
                    'id': str(lab_order.id),
                    'title': f"Lab Order {lab_order.order_number}",
                    'subtitle': f"{lab_order.patient.get_full_name()}",
                    'details': {
                        'order_date': lab_order.order_date.isoformat(),
                        'status': lab_order.status,
                        'doctor': lab_order.doctor.get_full_name(),
                        'serial': lab_order.serial_number,
                    },
                    'url': f'/laboratory/orders/{lab_order.id}/'
                })
            
            elif record_type == 'radiology_order':
                rad_order = RadiologyOrder.objects.get(id=record_id)
                results.append({
                    'type': 'radiology_order',
                    'id': str(rad_order.id),
                    'title': f"Radiology Order {rad_order.order_number}",
                    'subtitle': f"{rad_order.patient.get_full_name()}",
                    'details': {
                        'order_date': rad_order.order_date.isoformat(),
                        'status': rad_order.status,
                        'doctor': rad_order.ordering_doctor.get_full_name(),
                        'serial': rad_order.serial_number,
                    },
                    'url': f'/radiology/orders/{rad_order.id}/'
                })
            
            elif record_type == 'bill':
                bill = Invoice.objects.get(id=record_id)
                results.append({
                    'type': 'bill',
                    'id': str(bill.id),
                    'title': f"Bill {bill.bill_number}",
                    'subtitle': f"{bill.patient.get_full_name()}",
                    'details': {
                        'amount': str(bill.total_amount),
                        'status': bill.status,
                        'date': bill.created_at.isoformat(),
                        'serial': bill.serial_number,
                    },
                    'url': f'/billing/bills/{bill.id}/'
                })
            
        except Exception as e:
            logger.error(f"Error searching by QR data: {e}")
        
        return results
    
    def _search_by_text(self, query):
        """Search using text query across multiple models"""
        results = []
        query = query.strip().lower()
        
        if not query:
            return results
        
        # Search patients
        patients = Patient.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(patient_id__icontains=query) |
            Q(phone__icontains=query) |
            Q(email__icontains=query)
        )[:5]
        
        for patient in patients:
            results.append({
                'type': 'patient',
                'id': str(patient.id),
                'title': patient.get_full_name(),
                'subtitle': f"ID: {patient.patient_id}",
                'details': {
                    'phone': patient.phone,
                    'email': patient.email,
                },
                'url': f'/patients/{patient.id}/'
            })
        
        # Search doctors
        doctors = Doctor.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(phone__icontains=query) |
            Q(email__icontains=query)
        )[:5]
        
        for doctor in doctors:
            results.append({
                'type': 'doctor',
                'id': str(doctor.id),
                'title': doctor.get_full_name(),
                'subtitle': str(doctor.specialization) if doctor.specialization else '',
                'details': {
                    'department': str(doctor.department) if doctor.department else '',
                    'phone': doctor.phone,
                },
                'url': f'/doctors/{doctor.id}/'
            })
        
        # Search appointments by serial number or appointment number
        appointments = Appointment.objects.filter(
            Q(appointment_number__icontains=query) |
            Q(serial_number__icontains=query) |
            Q(patient__first_name__icontains=query) |
            Q(patient__last_name__icontains=query)
        )[:5]
        
        for appointment in appointments:
            results.append({
                'type': 'appointment',
                'id': str(appointment.id),
                'title': f"Appointment {appointment.appointment_number}",
                'subtitle': f"{appointment.patient.get_full_name()}",
                'details': {
                    'status': appointment.status,
                    'serial': appointment.serial_number,
                },
                'url': f'/appointments/{appointment.id}/'
            })
        
        # Search lab orders
        lab_orders = LabOrder.objects.filter(
            Q(order_number__icontains=query) |
            Q(serial_number__icontains=query) |
            Q(patient__first_name__icontains=query) |
            Q(patient__last_name__icontains=query)
        )[:5]
        
        for lab_order in lab_orders:
            results.append({
                'type': 'lab_order',
                'id': str(lab_order.id),
                'title': f"Lab Order {lab_order.order_number}",
                'subtitle': f"{lab_order.patient.get_full_name()}",
                'details': {
                    'status': lab_order.status,
                    'serial': lab_order.serial_number,
                },
                'url': f'/laboratory/orders/{lab_order.id}/'
            })
        
        # Search radiology orders
        rad_orders = RadiologyOrder.objects.filter(
            Q(order_number__icontains=query) |
            Q(serial_number__icontains=query) |
            Q(patient__first_name__icontains=query) |
            Q(patient__last_name__icontains=query)
        )[:5]
        
        for rad_order in rad_orders:
            results.append({
                'type': 'radiology_order',
                'id': str(rad_order.id),
                'title': f"Radiology Order {rad_order.order_number}",
                'subtitle': f"{rad_order.patient.get_full_name()}",
                'details': {
                    'status': rad_order.status,
                    'serial': rad_order.serial_number,
                },
                'url': f'/radiology/orders/{rad_order.id}/'
            })
        
        return results[:20]  # Limit total results
