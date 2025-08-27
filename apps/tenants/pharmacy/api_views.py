from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import F
from .models import Medicine, PharmacySale, PharmacySaleItem
from .serializers import MedicineSerializer, PharmacySaleSerializer, PharmacySaleItemSerializer

class MedicineViewSet(viewsets.ModelViewSet):
    queryset = Medicine.objects.all()
    serializer_class = MedicineSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()

class PharmacySaleViewSet(viewsets.ModelViewSet):
    queryset = PharmacySale.objects.all()
    serializer_class = PharmacySaleSerializer
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

            # Create PharmacySaleItem
            PharmacySaleItem.objects.create(
                sale=bill,
                medicine=medicine,
                quantity=quantity,
                unit_price=medicine.selling_price,
                total_amount=medicine.selling_price * quantity
            )

            # Reduce stock
            medicine.quantity_in_stock = F('quantity_in_stock') - quantity
            medicine.save()

            return Response({"success": "Item added to bill"}, status=status.HTTP_201_CREATED)

        except Medicine.DoesNotExist:
            return Response({"error": "Medicine not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'])
    def get_items(self, request, pk=None):
    sale = self.get_object()
    items = sale.items.all()
    serializer = PharmacySaleItemSerializer(items, many=True)
    return Response(serializer.data)
