from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import F
from .models import Medicine, PharmaceuticalBill, BillItem
from .serializers import MedicineSerializer, PharmaceuticalBillSerializer, BillItemSerializer

class MedicineViewSet(viewsets.ModelViewSet):
    queryset = Medicine.objects.all()
    serializer_class = MedicineSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()

class PharmaceuticalBillViewSet(viewsets.ModelViewSet):
    queryset = PharmaceuticalBill.objects.all()
    serializer_class = PharmaceuticalBillSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        bill = self.get_object()
        medicine_id = request.data.get('medicine_id')
        quantity = int(request.data.get('quantity'))

        try:
            medicine = Medicine.objects.get(id=medicine_id)
            if medicine.quantity_in_stock < quantity:
                return Response({"error": "Insufficient stock"}, status=status.HTTP_400_BAD_REQUEST)

            # Create BillItem
            BillItem.objects.create(
                bill=bill,
                medicine=medicine,
                quantity=quantity,
                price=medicine.price
            )

            # Reduce stock
            medicine.quantity_in_stock = F('quantity_in_stock') - quantity
            medicine.save()

            return Response({"success": "Item added to bill"}, status=status.HTTP_201_CREATED)

        except Medicine.DoesNotExist:
            return Response({"error": "Medicine not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'])
    def get_items(self, request, pk=None):
        bill = self.get_object()
        items = bill.items.all()
        serializer = BillItemSerializer(items, many=True)
        return Response(serializer.data)
