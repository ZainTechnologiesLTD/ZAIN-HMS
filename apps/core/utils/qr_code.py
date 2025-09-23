# apps/core/utils/qr_code.py
import qrcode
import json
import base64
from io import BytesIO
from django.conf import settings
from django.core.signing import Signer
from django.urls import reverse
from cryptography.fernet import Fernet
import logging

logger = logging.getLogger(__name__)

class QRCodeGenerator:
    """Utility class for generating QR codes with encrypted data"""
    
    def __init__(self):
        self.signer = Signer()
        # Use a simple encryption key (in production, store this securely)
        self.encryption_key = getattr(settings, 'QR_ENCRYPTION_KEY', Fernet.generate_key())
        self.cipher_suite = Fernet(self.encryption_key)
    
    def generate_qr_code(self, data, size='medium'):
        """
        Generate QR code for given data
        
        Args:
            data (dict): Data to encode in QR code
            size (str): Size of QR code ('small', 'medium', 'large')
        
        Returns:
            str: Base64 encoded image data
        """
        try:
            # Encrypt the data
            encrypted_data = self.encrypt_data(data)
            
            # Configure QR code based on size
            size_config = {
                'small': {'box_size': 8, 'border': 2},
                'medium': {'box_size': 10, 'border': 4},
                'large': {'box_size': 15, 'border': 6}
            }
            
            config = size_config.get(size, size_config['medium'])
            
            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=config['box_size'],
                border=config['border'],
            )
            
            qr.add_data(encrypted_data)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            return None
    
    def encrypt_data(self, data):
        """Encrypt data for QR code"""
        try:
            json_data = json.dumps(data)
            encrypted_data = self.cipher_suite.encrypt(json_data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Error encrypting data: {e}")
            return json.dumps(data)  # Fallback to unencrypted
    
    def decrypt_data(self, encrypted_data):
        """Decrypt data from QR code"""
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.cipher_suite.decrypt(decoded_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            logger.error(f"Error decrypting data: {e}")
            # Try to parse as unencrypted JSON
            try:
                return json.loads(encrypted_data)
            except:
                return None


class DocumentQRGenerator:
    """Specialized QR code generator for different document types"""
    
    def __init__(self):
        self.qr_gen = QRCodeGenerator()
    
    def generate_appointment_qr(self, appointment, request=None):
        """Generate QR code for appointment"""
        data = {
            'type': 'appointment',
            'id': str(appointment.id),
            'number': appointment.appointment_number,
            'patient_id': str(appointment.patient.id),
            'patient_name': appointment.patient.get_full_name(),
            'doctor_name': appointment.doctor.get_full_name(),
            'date': appointment.appointment_date.isoformat() if appointment.appointment_date else None,
            'time': appointment.appointment_time.isoformat() if appointment.appointment_time else None,
            'url': reverse('appointments:appointment_detail', kwargs={'pk': appointment.id}) if request else None
        }
        return self.qr_gen.generate_qr_code(data)
    
    def generate_lab_order_qr(self, lab_order, request=None):
        """Generate QR code for lab order"""
        data = {
            'type': 'lab_order',
            'id': str(lab_order.id),
            'number': lab_order.order_number,
            'patient_id': str(lab_order.patient.id),
            'patient_name': lab_order.patient.get_full_name(),
            'doctor_name': lab_order.doctor.get_full_name(),
            'order_date': lab_order.order_date.isoformat(),
            'status': lab_order.status,
            'url': reverse('laboratory:order_detail', kwargs={'pk': lab_order.id}) if request else None
        }
        return self.qr_gen.generate_qr_code(data)
    
    def generate_radiology_order_qr(self, radiology_order, request=None):
        """Generate QR code for radiology order"""
        data = {
            'type': 'radiology_order',
            'id': str(radiology_order.id),
            'number': radiology_order.order_number,
            'patient_id': str(radiology_order.patient.id),
            'patient_name': radiology_order.patient.get_full_name(),
            'doctor_name': radiology_order.ordering_doctor.get_full_name(),
            'order_date': radiology_order.order_date.isoformat(),
            'status': radiology_order.status,
            'url': reverse('radiology:order_detail', kwargs={'pk': radiology_order.id}) if request else None
        }
        return self.qr_gen.generate_qr_code(data)
    
    def generate_bill_qr(self, bill, request=None):
        """Generate QR code for bill"""
        data = {
            'type': 'bill',
            'id': str(bill.id),
            'number': bill.bill_number,
            'patient_id': str(bill.patient.id),
            'patient_name': bill.patient.get_full_name(),
            'amount': str(bill.total_amount),
            'status': bill.status,
            'date': bill.created_at.isoformat(),
            'url': reverse('billing:bill_detail', kwargs={'pk': bill.id}) if request else None
        }
        return self.qr_gen.generate_qr_code(data)
    
    def generate_patient_qr(self, patient, request=None):
        """Generate QR code for patient"""
        data = {
            'type': 'patient',
            'id': str(patient.id),
            'patient_id': patient.patient_id,
            'name': patient.get_full_name(),
            'phone': patient.phone,
            'email': patient.email,
            'blood_group': patient.blood_group,
            'url': reverse('patients:patient_detail', kwargs={'pk': patient.id}) if request else None
        }
        return self.qr_gen.generate_qr_code(data)
    
    def generate_doctor_qr(self, doctor, request=None):
        """Generate QR code for doctor"""
        data = {
            'type': 'doctor',
            'id': str(doctor.id),
            'name': doctor.get_full_name(),
            'specialization': doctor.specialization if hasattr(doctor, 'specialization') else None,
            'phone': getattr(doctor, 'phone', getattr(doctor, 'phone_number', None)),
            'email': doctor.email,
            'url': reverse('doctors:doctor_detail', kwargs={'pk': doctor.id}) if request else None
        }
        return self.qr_gen.generate_qr_code(data)


# Global instances
qr_generator = QRCodeGenerator()
document_qr_generator = DocumentQRGenerator()
