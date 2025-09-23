from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.

@login_required
def inventory_dashboard(request):
    """Inventory Dashboard view"""
    context = {
        'title': 'Inventory Management',
        'page_title': 'Inventory Dashboard',
    }
    return render(request, 'inventory/dashboard.html', context)
