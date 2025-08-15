from rest_framework import viewsets
from .models import LabTest, LabResult
from .serializers import LabTestSerializer, LabResultSerializer
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.mixins import LoginRequiredMixin

class LabTestViewSet(LoginRequiredMixin, viewsets.ModelViewSet):
    queryset = LabTest.objects.all()
    serializer_class = LabTestSerializer

    def get_queryset(self):
        queryset = LabTest.objects.all()
        patient_id = self.request.query_params.get('patient_id', None)
        doctor_id = self.request.query_params.get('doctor_id', None)
        if patient_id is not None:
            queryset = queryset.filter(patient_id=patient_id)
        if doctor_id is not None:
            queryset = queryset.filter(referred_doctor_id=doctor_id)
        return queryset
    
def diagnostic_list(request):
    """View to render the diagnostic list."""
    diagnostics = LabTest.objects.all()  # Or fetch relevant diagnostics data
    return render(request, 'diagnostics/diagnostic_list.html', {'diagnostics': diagnostics})    

def lab_test_list(request):
    lab_tests = LabTest.objects.all()
    return render(request, 'diagnostics/lab_test_list.html', {'lab_tests': lab_tests})

class LabResultViewSet(LoginRequiredMixin, viewsets.ModelViewSet):
    queryset = LabResult.objects.all()
    serializer_class = LabResultSerializer

    def get_queryset(self):
        queryset = LabResult.objects.all()
        patient_id = self.request.query_params.get('patient_id', None)
        doctor_id = self.request.query_params.get('doctor_id', None)
        if patient_id is not None:
            queryset = queryset.filter(patient_id=patient_id)
        if doctor_id is not None:
            queryset = queryset.filter(test__referred_doctor_id=doctor_id)
        return queryset

def lab_result_list(request, lab_test_id):
    lab_test = get_object_or_404(LabTest, id=lab_test_id)
    lab_results = LabResult.objects.filter(test=lab_test)
    return render(request, 'diagnostics/lab_result_list.html', {'lab_results': lab_results, 'lab_test': lab_test})