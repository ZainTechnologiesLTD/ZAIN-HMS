# doctors/views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from .models import Doctor


class DoctorListView(LoginRequiredMixin, ListView):
    model = Doctor
    template_name = 'doctors/doctor_list.html'
    context_object_name = 'doctors'

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
           
                return queryset.filter(user=self.request.user)
        return queryset

class DoctorDetailView(LoginRequiredMixin, DetailView):
    template_name = 'doctors/doctor_detail.html'

class DoctorCreateView(LoginRequiredMixin, CreateView):
    template_name = 'doctors/doctor_form.html'
    success_url = reverse_lazy('doctor_list')
    success_message = "Doctor profile created successfully"
    fields = [
        'first_name', 'last_name', 'specialization', 'license_number',
        'phone_number', 'email', 'date_of_birth', 'address',
        'joining_date', 'is_active'
    ]

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class DoctorUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'doctors/doctor_form.html'
    success_url = reverse_lazy('doctor_list')
    success_message = "Doctor profile updated successfully"
    fields = [
        'first_name', 'last_name', 'specialization', 'license_number',
        'phone_number', 'email', 'date_of_birth', 'address',
        'joining_date', 'is_active'
    ]