# billing/views.py
from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from xhtml2pdf import pisa
from django.template.loader import get_template, render_to_string
from .models import Bill
from .serializers import BillSerializer
from patients.models import Patient
from appointments.models import Appointment
from diagnostics.models import LabTest

class BillViewSet(viewsets.ModelViewSet):
    queryset = Bill.objects.all()
    serializer_class = BillSerializer

    def perform_create(self, serializer):
        # Automatically calculate the total and generate the detailed bill
        bill = serializer.save()  # Save the Bill instance
        bill.generate_detailed_bill()  # Update the detailed bill text
        bill.save(update_fields=['total_amount', 'detailed_bill_text'])

    def perform_update(self, serializer):
        # When updating, regenerate the detailed bill
        bill = serializer.save()  # Save changes to the Bill instance
        bill.generate_detailed_bill()  # Update the detailed bill text
        bill.save(update_fields=['total_amount', 'detailed_bill_text'])

    @action(detail=True, methods=['get'])
    def print_bill(self, request, pk=None):
        """
        API endpoint to generate and return the bill as an HTML response.
        """
        bill = get_object_or_404(Bill, pk=pk)
        return render(request, 'billing/print_bill.html', {'bill': bill})

    @action(detail=True, methods=['get'])
    def print_bill_pdf(self, request, pk=None):
        """
        API endpoint to generate and return the bill as a PDF.
        """
        bill = get_object_or_404(Bill, pk=pk)
        return self.render_to_pdf('billing/print_bill.html', {'bill': bill})

    def render_to_pdf(self, template_src, context_dict):
        """
        Helper function to generate PDF from an HTML template.
        """
        template = get_template(template_src)
        html = template.render(context_dict)
        result = HttpResponse(content_type='application/pdf')
        pisa_status = pisa.CreatePDF(html, dest=result)
        if pisa_status.err:
            return HttpResponse('Error generating PDF: <pre>' + html + '</pre>')
        return result

    @action(detail=False, methods=['get'])
    def quick_invoice(self, request):
        """
        Returns a form for quick invoice creation
        """
        patients = Patient.objects.all()
        appointments = Appointment.objects.filter(status='COMPLETED')
        lab_tests = LabTest.objects.all()
        
        context = {
            'patients': patients,
            'appointments': appointments,
            'lab_tests': lab_tests,
        }
        
        html = render_to_string('billing/quick_invoice_form.html', context)
        return Response(html)

    @action(detail=False, methods=['post'])
    def create_quick_invoice(self, request):
        """
        Creates a bill from the quick invoice form
        """
        try:
            patient_id = request.data.get('patient')
            appointment_ids = request.data.getlist('appointments')
            lab_test_ids = request.data.getlist('lab_tests')
            hospital_charges = request.data.get('hospital_charges', 0)

            # Create new bill
            bill = Bill.objects.create(
                patient_id=patient_id,
                hospital_charges=hospital_charges
            )

            # Add appointments and lab tests
            if appointment_ids:
                bill.appointments.set(appointment_ids)
            if lab_test_ids:
                bill.diagnostic_tests.set(lab_test_ids)

            # Save to trigger the signal that calculates totals
            bill.save()

            return Response({
                'status': 'success',
                'message': 'Invoice created successfully',
                'bill_id': bill.id
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)