from django.shortcuts import render, get_object_or_404
from .models import PharmaceuticalBill

def bill_list_view(request):
    """
    Render a list of pharmaceutical bills.
    """
    bills = PharmaceuticalBill.objects.all().order_by('-created_at')  # Latest bills first
    return render(request, 'pharmaceuticals/medicine_list.html', {'bills': bills})

def bill_detail_view(request, bill_id):
    """
    Render details of a specific pharmaceutical bill.
    """
    bill = get_object_or_404(PharmaceuticalBill, id=bill_id)
    return render(request, 'pharmaceuticals/bill_detail.html', {'bill': bill})
