# apps/core/utils/barcode_generator.py
import os
import io
import base64
from barcode import Code128, Code39, EAN13, EAN8, UPCA
from barcode.writer import ImageWriter
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.signing import Signer
from cryptography.fernet import Fernet
from datetime import datetime
import uuid

class BarcodeGenerator:
    """
    Modern hospital barcode generation system
    Supports multiple barcode formats commonly used in healthcare
    """
    
    # Hospital barcode formats
    BARCODE_FORMATS = {
        'CODE128': Code128,  # Most versatile, supports alphanumeric
        'CODE39': Code39,    # Common in healthcare
        'EAN13': EAN13,      # 13-digit numeric
        'EAN8': EAN8,        # 8-digit numeric
        'UPCA': UPCA,        # 12-digit numeric
    }
    
    def __init__(self):
        self.signer = Signer()
        # Use Django secret key for encryption
        secret_key = settings.SECRET_KEY.encode()[:32].ljust(32, b'0')
        self.cipher = Fernet(base64.urlsafe_b64encode(secret_key))
        
    def generate_barcode_data(self, object_type, object_id, hospital_code="HMS01"):
        """
        Generate barcode data for hospital objects
        Format: {hospital_code}-{type}-{year}-{sequence}
        """
        current_year = datetime.now().year
        
        # Create a unique identifier for the barcode
        if hasattr(object_id, 'hex'):
            # If it's a UUID, use a portion of it
            short_id = str(object_id).replace('-', '')[:8].upper()
        else:
            short_id = str(object_id)[:8].upper()
            
        # Generate barcode data
        barcode_data = f"{hospital_code}{object_type[:3].upper()}{current_year}{short_id}"
        
        return barcode_data
    
    def generate_barcode(self, data, format_type='CODE128', save_path=None):
        """
        Generate barcode image
        """
        try:
            if format_type not in self.BARCODE_FORMATS:
                format_type = 'CODE128'  # Default to CODE128
                
            barcode_class = self.BARCODE_FORMATS[format_type]
            
            # Create barcode with image writer
            barcode = barcode_class(data, writer=ImageWriter())
            
            if save_path:
                # Save to file
                barcode.save(save_path)
                return save_path
            else:
                # Return as base64 for embedding
                buffer = io.BytesIO()
                barcode.write(buffer)
                buffer.seek(0)
                
                # Convert to base64
                barcode_base64 = base64.b64encode(buffer.read()).decode('utf-8')
                return f"data:image/png;base64,{barcode_base64}"
                
        except Exception as e:
            print(f"Barcode generation error: {e}")
            return None
    
    def encrypt_barcode_data(self, data):
        """Encrypt barcode data for security"""
        try:
            encrypted_data = self.cipher.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            print(f"Encryption error: {e}")
            return data
    
    def decrypt_barcode_data(self, encrypted_data):
        """Decrypt barcode data"""
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.cipher.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            print(f"Decryption error: {e}")
            return encrypted_data


class DocumentBarcodeGenerator:
    """
    Hospital document-specific barcode generator
    """
    
    def __init__(self):
        self.generator = BarcodeGenerator()
    
    def generate_patient_barcode(self, patient):
        """Generate barcode for patient records"""
        data = self.generator.generate_barcode_data('PAT', patient.id)
        return self.generator.generate_barcode(data)
    
    def generate_doctor_barcode(self, doctor):
        """Generate barcode for doctor records"""
        data = self.generator.generate_barcode_data('DOC', doctor.id)
        return self.generator.generate_barcode(data)
    
    def generate_appointment_barcode(self, appointment):
        """Generate barcode for appointment records"""
        # Use serial number if available
        if hasattr(appointment, 'serial_number') and appointment.serial_number:
            data = appointment.serial_number.replace('-', '')
        else:
            data = self.generator.generate_barcode_data('APT', appointment.id)
        return self.generator.generate_barcode(data)
    
    def generate_lab_order_barcode(self, lab_order):
        """Generate barcode for laboratory orders"""
        if hasattr(lab_order, 'serial_number') and lab_order.serial_number:
            data = lab_order.serial_number.replace('-', '')
        else:
            data = self.generator.generate_barcode_data('LAB', lab_order.id)
        return self.generator.generate_barcode(data)
    
    def generate_radiology_order_barcode(self, radiology_order):
        """Generate barcode for radiology orders"""
        if hasattr(radiology_order, 'serial_number') and radiology_order.serial_number:
            data = radiology_order.serial_number.replace('-', '')
        else:
            data = self.generator.generate_barcode_data('RAD', radiology_order.id)
        return self.generator.generate_barcode(data)
    
    def generate_invoice_barcode(self, invoice):
        """Generate barcode for invoices/bills"""
        if hasattr(invoice, 'serial_number') and invoice.serial_number:
            data = invoice.serial_number.replace('-', '')
        else:
            data = self.generator.generate_barcode_data('BIL', invoice.id)
        return self.generator.generate_barcode(data)
    
    def generate_prescription_barcode(self, prescription):
        """Generate barcode for prescriptions"""
        if hasattr(prescription, 'serial_number') and prescription.serial_number:
            data = prescription.serial_number.replace('-', '')
        else:
            data = self.generator.generate_barcode_data('PRE', prescription.id)
        return self.generator.generate_barcode(data)


# Hospital barcode scanner data parser
class BarcodeScanner:
    """
    Parse scanned barcode data and search hospital records
    """
    
    @staticmethod
    def parse_barcode_data(barcode_data):
        """
        Parse hospital barcode data
        Expected formats:
        - HMS01APT2025XXXXXXXX (Appointment)
        - HMS01LAB2025XXXXXXXX (Lab Order)
        - HMS01RAD2025XXXXXXXX (Radiology Order)
        - HMS01BIL2025XXXXXXXX (Bill/Invoice)
        - HMS01PAT2025XXXXXXXX (Patient)
        - HMS01DOC2025XXXXXXXX (Doctor)
        """
        
        if not barcode_data or len(barcode_data) < 10:
            return None
            
        try:
            # Extract components
            hospital_code = barcode_data[:5]  # HMS01
            doc_type = barcode_data[5:8]      # APT, LAB, RAD, etc.
            year = barcode_data[8:12]         # 2025
            identifier = barcode_data[12:]    # Remaining part
            
            return {
                'hospital_code': hospital_code,
                'document_type': doc_type,
                'year': year,
                'identifier': identifier,
                'full_data': barcode_data
            }
        except Exception as e:
            print(f"Barcode parsing error: {e}")
            return None
    
    @staticmethod
    def search_by_barcode(barcode_data):
        """
        Search hospital records by barcode data
        """
        from apps.patients.models import Patient
        from apps.doctors.models import Doctor
        from apps.appointments.models import Appointment
        from apps.laboratory.models import LabOrder
        from apps.radiology.models import RadiologyOrder
        from apps.billing.models import Invoice
        
        parsed = BarcodeScanner.parse_barcode_data(barcode_data)
        if not parsed:
            return None
            
        doc_type = parsed['document_type']
        results = []
        
        try:
            if doc_type == 'APT':
                # Search appointments by serial number or ID
                appointments = Appointment.objects.filter(
                    serial_number__icontains=barcode_data
                )[:5]
                for apt in appointments:
                    results.append({
                        'type': 'appointment',
                        'object': apt,
                        'title': f"Appointment - {apt.patient.user.get_full_name()}",
                        'subtitle': f"Dr. {apt.doctor.user.get_full_name()} - {apt.appointment_date}",
                        'url': f'/appointments/{apt.id}/'
                    })
                    
            elif doc_type == 'LAB':
                # Search lab orders
                lab_orders = LabOrder.objects.filter(
                    serial_number__icontains=barcode_data
                )[:5]
                for lab in lab_orders:
                    results.append({
                        'type': 'lab_order',
                        'object': lab,
                        'title': f"Lab Order - {lab.patient.user.get_full_name()}",
                        'subtitle': f"Ordered: {lab.created_at.date()}",
                        'url': f'/laboratory/orders/{lab.id}/'
                    })
                    
            elif doc_type == 'RAD':
                # Search radiology orders
                rad_orders = RadiologyOrder.objects.filter(
                    serial_number__icontains=barcode_data
                )[:5]
                for rad in rad_orders:
                    results.append({
                        'type': 'radiology_order',
                        'object': rad,
                        'title': f"Radiology Order - {rad.patient.user.get_full_name()}",
                        'subtitle': f"Ordered: {rad.created_at.date()}",
                        'url': f'/radiology/orders/{rad.id}/'
                    })
                    
            elif doc_type == 'BIL':
                # Search bills/invoices
                invoices = Invoice.objects.filter(
                    serial_number__icontains=barcode_data
                )[:5]
                for inv in invoices:
                    results.append({
                        'type': 'invoice',
                        'object': inv,
                        'title': f"Bill #{inv.invoice_number} - {inv.patient.user.get_full_name()}",
                        'subtitle': f"Amount: ${inv.total_amount} - {inv.get_status_display()}",
                        'url': f'/billing/bill/{inv.id}/'
                    })
                    
            elif doc_type == 'PAT':
                # Search patients
                patients = Patient.objects.filter(
                    patient_id__icontains=parsed['identifier']
                )[:5]
                for patient in patients:
                    results.append({
                        'type': 'patient',
                        'object': patient,
                        'title': f"Patient - {patient.user.get_full_name()}",
                        'subtitle': f"ID: {patient.patient_id} - Phone: {patient.phone}",
                        'url': f'/patients/{patient.id}/'
                    })
                    
            elif doc_type == 'DOC':
                # Search doctors
                doctors = Doctor.objects.filter(
                    employee_id__icontains=parsed['identifier']
                )[:5]
                for doctor in doctors:
                    results.append({
                        'type': 'doctor',
                        'object': doctor,
                        'title': f"Dr. {doctor.user.get_full_name()}",
                        'subtitle': f"ID: {doctor.employee_id} - {doctor.specialization}",
                        'url': f'/doctors/{doctor.id}/'
                    })
                    
        except Exception as e:
            print(f"Barcode search error: {e}")
            
        return results
