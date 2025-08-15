from django.db import models
from django.utils import timezone
from appointments.models import Appointment
from laboratory.models import LabTest
from patients.models import Patient
from django.db.models.signals import post_save
from django.dispatch import receiver

class Bill(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='bills')
    appointments = models.ManyToManyField(Appointment, blank=True, related_name='bills')
    diagnostic_tests = models.ManyToManyField(LabTest, blank=True, related_name='bills')
    hospital_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=[('Paid', 'Paid'), ('Unpaid', 'Unpaid')], default='Unpaid')
    
    # Field to store the detailed bill in a formatted string
    detailed_bill_text = models.TextField(blank=True)

    def __str__(self):
        return f"Bill for {self.patient} - ${self.total_amount}"

    def generate_detailed_bill(self):
        """Generates a formatted bill string."""
        details = []

    # Include details of appointments
        if self.appointments.exists():
            for appointment in self.appointments.all():
            # Ensure appointment.doctor is a Doctor instance
                doctor_name = appointment.doctor.name if hasattr(appointment.doctor, 'name') else 'Unknown Doctor'
            details.append(f"Appointment with Dr. {doctor_name}: ${appointment.fee}")

    # Include details of diagnostic tests
        if self.diagnostic_tests.exists():
            for test in self.diagnostic_tests.all():
             details.append(f"Lab Test '{test.test_name}': ${test.price}")

    # Add hospital charges if applicable
        if self.hospital_charges > 0:
            details.append(f"Hospital Charges: ${self.hospital_charges}")

    # Join all details and return
        return "\n".join(details)


# Signal to calculate total amount after a Bill is saved and store the detailed bill
@receiver(post_save, sender=Bill)
def calculate_total_and_store_bill(sender, instance, **kwargs):
    total = 0
    
    # Sum the fees from all appointments
    for appointment in instance.appointments.all():
        total += appointment.fee
    
    # Sum the prices from all diagnostic tests
    for test in instance.diagnostic_tests.all():
        total += test.price
    
    # Add hospital charges, if any
    total += instance.hospital_charges
    
    # Update total_amount and detailed_bill_text, then save
    detailed_bill = instance.generate_detailed_bill()
    if total != instance.total_amount or detailed_bill != instance.detailed_bill_text:
        instance.total_amount = total
        instance.detailed_bill_text = detailed_bill
        instance.save(update_fields=['total_amount', 'detailed_bill_text'])
