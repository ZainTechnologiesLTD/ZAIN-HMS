from django.db import models
from django.conf import settings  # Use AUTH_USER_MODEL reference
from decimal import Decimal

class Medicine(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_in_stock = models.PositiveIntegerField()
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class PharmaceuticalBill(models.Model):
    # Reference the user model properly
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='pharmaceutical_bills'
    )
    customer_name = models.CharField(max_length=100)
    customer_mobile = models.CharField(max_length=15)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Bill {self.id} - {self.customer_name}"

    def calculate_total(self):
        """
        Recalculate the total amount based on bill items.
        """
        total = sum(item.get_total_price() for item in self.items.all())
        self.total_amount = total
        self.save()

class BillItem(models.Model):
    bill = models.ForeignKey(
        PharmaceuticalBill, 
        related_name='items', 
        on_delete=models.CASCADE
    )
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def get_total_price(self):
        return self.quantity * self.price

    def __str__(self):
        return f"{self.medicine.name} - {self.quantity} units"
