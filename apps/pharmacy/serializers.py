from rest_framework import serializers
from .models import Medicine, PharmacySale, PharmacySaleItem

class MedicineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medicine
        fields = '__all__'

class PharmacySaleItemSerializer(serializers.ModelSerializer):
    medicine_name = serializers.ReadOnlyField(source='medicine.name')
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = PharmacySaleItem
        fields = ['medicine', 'medicine_name', 'quantity', 'unit_price', 'total_amount']

    def get_total_price(self, obj):
        return obj.total_amount

class PharmacySaleSerializer(serializers.ModelSerializer):
    items = PharmacySaleItemSerializer(many=True, read_only=True)

    class Meta:
        model = PharmacySale
        fields = '__all__'
