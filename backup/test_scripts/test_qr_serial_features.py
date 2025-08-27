#!/usr/bin/env python3
"""
Test script for QR Code and Serial Number functionality
Run this after starting the Django server to test the new features
"""

import os
import sys
import django

# Add the project root to Python path
sys.path.insert(0, '/home/mehedi/Projects/zain_hms')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zain_hms.settings')
django.setup()

from apps.core.utils.qr_code import document_qr_generator, qr_generator
from apps.core.utils.serial_number import SerialNumberGenerator, get_serial_number_stats
from apps.appointments.models import Appointment
from apps.patients.models import Patient
from apps.doctors.models import Doctor

def test_serial_numbers():
    """Test serial number generation"""
    print("🔢 Testing Serial Number Generation...")
    
    # Test different document types
    test_types = ['appointment', 'lab_order', 'radiology_order', 'bill']
    
    for doc_type in test_types:
        serial = SerialNumberGenerator.generate_serial_number(doc_type, 'HMS01')
        print(f"  ✅ {doc_type.title()}: {serial}")
    
    # Test stats
    stats = get_serial_number_stats('HMS01')
    print("\n📊 Serial Number Statistics:")
    for doc_type, data in stats.items():
        print(f"  {doc_type}: {data['prefix']}-2025-{data['next_number']:06d} (next)")

def test_qr_codes():
    """Test QR code generation"""
    print("\n🔗 Testing QR Code Generation...")
    
    # Test basic QR code
    test_data = {
        'type': 'test',
        'message': 'Hello, QR World!',
        'timestamp': '2025-08-18'
    }
    
    qr_code = qr_generator.generate_qr_code(test_data)
    if qr_code:
        print("  ✅ Basic QR code generation: SUCCESS")
        print(f"  📏 QR code length: {len(qr_code)} characters")
    else:
        print("  ❌ Basic QR code generation: FAILED")
    
    # Test encryption/decryption
    encrypted = qr_generator.encrypt_data(test_data)
    decrypted = qr_generator.decrypt_data(encrypted)
    
    if decrypted == test_data:
        print("  ✅ QR code encryption/decryption: SUCCESS")
    else:
        print("  ❌ QR code encryption/decryption: FAILED")

def test_database_records():
    """Test with actual database records if available"""
    print("\n💾 Testing with Database Records...")
    
    # Test with patients
    patient_count = Patient.objects.count()
    print(f"  📋 Found {patient_count} patients in database")
    
    if patient_count > 0:
        patient = Patient.objects.first()
        patient_qr = document_qr_generator.generate_patient_qr(patient)
        if patient_qr:
            print(f"  ✅ Patient QR code generated for: {patient.get_full_name()}")
        else:
            print(f"  ❌ Failed to generate QR code for patient: {patient.get_full_name()}")
    
    # Test with doctors
    doctor_count = Doctor.objects.count()
    print(f"  👨‍⚕️ Found {doctor_count} doctors in database")
    
    if doctor_count > 0:
        doctor = Doctor.objects.first()
        doctor_qr = document_qr_generator.generate_doctor_qr(doctor)
        if doctor_qr:
            print(f"  ✅ Doctor QR code generated for: Dr. {doctor.get_full_name()}")
        else:
            print(f"  ❌ Failed to generate QR code for doctor: Dr. {doctor.get_full_name()}")
    
    # Test with appointments
    appointment_count = Appointment.objects.count()
    print(f"  📅 Found {appointment_count} appointments in database")
    
    if appointment_count > 0:
        appointment = Appointment.objects.first()
        appointment_qr = document_qr_generator.generate_appointment_qr(appointment)
        if appointment_qr:
            print(f"  ✅ Appointment QR code generated for: {appointment.appointment_number}")
            print(f"  🔢 Appointment serial: {appointment.serial_number}")
        else:
            print(f"  ❌ Failed to generate QR code for appointment: {appointment.appointment_number}")

def main():
    """Main test function"""
    print("🚀 ZAIN HMS - QR Code & Serial Number Test Suite")
    print("=" * 60)
    
    try:
        test_serial_numbers()
        test_qr_codes()
        test_database_records()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETED!")
        print("\n📝 Next Steps:")
        print("1. Visit http://localhost:8000 to access the system")
        print("2. Navigate to 'Barcode Scanner' to test scanning functionality")
        print("3. Create new appointments to test serial number generation")
        print("4. Print documents to see QR codes and serial numbers")
        print("5. Use language switcher to test multi-language support")
        print("6. Visit http://localhost:8000/rosetta/ to manage translations")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
