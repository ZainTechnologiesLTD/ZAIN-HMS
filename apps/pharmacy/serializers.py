from rest_framework import serializers
from .models import Medicine, PharmaceuticalBill, BillItem

class MedicineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medicine
        fields = '__all__'

class BillItemSerializer(serializers.ModelSerializer):
    medicine_name = serializers.ReadOnlyField(source='medicine.name')
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = BillItem
        fields = ['medicine', 'medicine_name', 'quantity', 'price', 'total_price']

    def get_total_price(self, obj):
        return obj.get_total_price()

class PharmaceuticalBillSerializer(serializers.ModelSerializer):
    items = BillItemSerializer(many=True, read_only=True)

    class Meta:
        model = PharmaceuticalBill
        fields = ['id', 'customer_name', 'customer_mobile', 'total_amount', 'created_by', 'created_at', 'items']
