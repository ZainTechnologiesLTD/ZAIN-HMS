# opd/views.py
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q
from django.contrib import messages
from django.shortcuts import redirect
from .models import OPD
from .forms import OPDForm  # You'll need to create this form

class OPDListView(LoginRequiredMixin, ListView):
    model = OPD
    template_name = 'opd/opd_list.html'
    context_object_name = 'opd_records'
    paginate_by = 10

    def get_queryset(self):
        queryset = OPD.objects.all()
        search = self.request.GET.get('search', '')
        status = self.request.GET.get('status', '')
        priority = self.request.GET.get('priority', '')

        if search:
            queryset = queryset.filter(
                Q(patient_name__icontains=search) |
                Q(patient_phone__icontains=search) |
                Q(doctor__username__icontains=search)
            )
        
        if status:
            queryset = queryset.filter(status=status)
            
        if priority:
            queryset = queryset.filter(priority=priority)

        return queryset.select_related('doctor')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['current_priority'] = self.request.GET.get('priority', '')
        return context

class OPDCreateView(LoginRequiredMixin, CreateView):
    model = OPD
    form_class = OPDForm
    template_name = 'opd/opd_form.html'
    success_url = reverse_lazy('opd:opd_list')

    def form_valid(self, form):
        form.instance.doctor = self.request.user
        messages.success(self.request, 'OPD record created successfully.')
        return super().form_valid(form)

class OPDUpdateView(LoginRequiredMixin, UpdateView):
    model = OPD
    form_class = OPDForm
    template_name = 'opd/opd_form.html'
    success_url = reverse_lazy('opd:opd_list')

    def form_valid(self, form):
        messages.success(self.request, 'OPD record updated successfully.')
        return super().form_valid(form)

class OPDDetailView(LoginRequiredMixin, DetailView):
    model = OPD
    template_name = 'opd/opd_detail.html'
    context_object_name = 'opd'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add any additional context data here
        return context

class OPDDeleteView(LoginRequiredMixin, DeleteView):
    model = OPD
    template_name = 'opd/opd_confirm_delete.html'
    success_url = reverse_lazy('opd:opd_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'OPD record deleted successfully.')
        return super().delete(request, *args, **kwargs)

# Additional Views for HTMX support

from django.http import HttpResponse
from django.template.loader import render_to_string

def opd_search(request):
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    priority = request.GET.get('priority', '')
    
    queryset = OPD.objects.all()
    
    if search:
        queryset = queryset.filter(
            Q(patient_name__icontains=search) |
            Q(patient_phone__icontains=search)
        )
    
    if status:
        queryset = queryset.filter(status=status)
        
    if priority:
        queryset = queryset.filter(priority=priority)
        
    context = {
        'opd_records': queryset.select_related('doctor')[:10]
    }
    
    html = render_to_string('opd/includes/opd_list_table.html', context)
    return HttpResponse(html)

def toggle_payment_status(request, pk):
    opd = OPD.objects.get(pk=pk)
    opd.is_paid = not opd.is_paid
    opd.save()
    
    return HttpResponse(
        f'<span class="px-2 py-1 rounded-full text-sm '
        f'{"bg-green-100 text-green-800" if opd.is_paid else "bg-red-100 text-red-800"}">'
        f'{"Paid" if opd.is_paid else "Unpaid"}</span>'
    )