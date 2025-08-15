from rest_framework import serializers
from .models import LabTest, LabResult

class LabTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabTest
        fields = ['id','patient', 'test_name', 'description', 'price']

class LabResultSerializer(serializers.ModelSerializer):
    test_name = serializers.CharField(source='test.name', read_only=True)

    class Meta:
        model = LabResult
        fields = ['id', 'patient', 'test', 'result', 'date_performed', 'technician']
        read_only_fields = ['date_performed']