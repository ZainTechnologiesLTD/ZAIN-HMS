from django.shortcuts import render

def surgery_list_view(request):
    """
    Display a list of surgeries (placeholder view).
    """
    return render(request, 'surgery/surgery_list.html')
