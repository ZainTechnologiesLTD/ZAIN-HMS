# ipd/views.py
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.core.mixins import RequireHospitalSelectionMixin
from django.urls import reverse_lazy
from .models import IPDRecord
from .forms import IPDRecordForm

class IPDListView(LoginRequiredMixin, ListView):
    model = IPDRecord
    template_name = 'ipd/ipd_list.html'
    context_object_name = 'ipd_records'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset.select_related('patient', 'doctor', 'room', 'bed')

class IPDCreateView(RequireHospitalSelectionMixin, LoginRequiredMixin, CreateView):
    model = IPDRecord
    form_class = IPDRecordForm
    template_name = 'ipd/ipd_form.html'
    success_url = reverse_lazy('ipd:ipd_list')

class IPDDetailView(LoginRequiredMixin, DetailView):
    model = IPDRecord
    template_name = 'ipd/ipd_detail.html'
    context_object_name = 'ipd_record'

class IPDUpdateView(LoginRequiredMixin, UpdateView):
    model = IPDRecord
    form_class = IPDRecordForm
    template_name = 'ipd/ipd_form.html'
    success_url = reverse_lazy('ipd:ipd_list')

class IPDDeleteView(LoginRequiredMixin, DeleteView):
    model = IPDRecord
    template_name = 'ipd/ipd_confirm_delete.html'
    success_url = reverse_lazy('ipd:ipd_list')
