from rest_framework import serializers
from apps.patients.models import Patient
from apps.appointments.models import Appointment
from apps.laboratory.models import LabTest
from apps.billing.models import Bill

class BillSerializer(serializers.ModelSerializer):
    # Handle many-to-many relationships properly
    diagnostic_tests = serializers.PrimaryKeyRelatedField(queryset=LabTest.objects.all(), many=True, required=False, allow_null=True)
    appointments = serializers.PrimaryKeyRelatedField(queryset=Appointment.objects.all(), many=True, required=False, allow_null=True)

    class Meta:
        model = Bill
        fields = '__all__'

    def create(self, validated_data):
        diagnostic_tests_data = validated_data.pop('diagnostic_tests', [])
        appointments_data = validated_data.pop('appointments', [])
        
        # Create Bill instance
        bill = Bill.objects.create(**validated_data)

        # Handle many-to-many relationships
        if diagnostic_tests_data:
            bill.diagnostic_tests.set(diagnostic_tests_data)
        if appointments_data:
            bill.appointments.set(appointments_data)

        return bill

    def update(self, instance, validated_data):
        diagnostic_tests_data = validated_data.pop('diagnostic_tests', [])
        appointments_data = validated_data.pop('appointments', [])

        # Update the Bill instance
        instance = super().update(instance, validated_data)

        # Handle many-to-many relationships
        if diagnostic_tests_data:
            instance.diagnostic_tests.set(diagnostic_tests_data)
        if appointments_data:
            instance.appointments.set(appointments_data)

        return instance
