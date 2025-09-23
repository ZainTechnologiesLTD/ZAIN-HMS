from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.

@login_required
def hr_dashboard(request):
    """HR Dashboard view"""
    context = {
        'title': 'Human Resources',
        'page_title': 'HR Dashboard',
    }
    return render(request, 'hr/dashboard.html', context)
