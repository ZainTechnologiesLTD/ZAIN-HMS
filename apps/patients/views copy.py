# patients/views.py
from pyexpat.errors import messages
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Patient
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q


class PatientListView(LoginRequiredMixin, ListView):
    model = Patient  # Add this line
    template_name = 'patients/patient_list.html'
    context_object_name = 'patients'
    paginate_by = 10

    def get_queryset(self):
        queryset = Patient.objects.all()
        # Search functionality
        search_query = self.request.GET.get('q', '')
        if search_query:
            queryset = queryset.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(patient_id__icontains=search_query) |
                Q(email__icontains=search_query)
            )
        
        return queryset

class PatientDetailView(LoginRequiredMixin, DetailView):
    template_name = 'patients/patient_detail.html'
    required_permission = 'patients.can_access_medical_history'

class PatientCreateView(LoginRequiredMixin, CreateView):
    template_name = 'patients/patient_form.html'
    model = Patient  # Add this line
    success_url = reverse_lazy('patients:patient_list')
    success_message = "Patient record created successfully"
    fields = [
        'first_name', 'last_name', 'gender', 'phone_number', 'email',
        'date_of_birth', 'address', 'blood_type', 'allergies',
        'medical_conditions', 'medications', 'emergency_contact_name',
        'emergency_contact_phone'
    ]

class PatientQuickAddView(LoginRequiredMixin, CreateView):
    template_name = 'patients/quick_add.html'
    model = Patient
  
    fields = [
        'first_name', 'last_name', 'gender', 'phone_number', 
        'email', 'date_of_birth', 'blood_type', 'address',
        'allergies', 'medical_conditions', 'medications',
        'emergency_contact_name', 'emergency_contact_phone'
    ]
    success_message = "Patient %(first_name)s %(last_name)s was added successfully!"

    def form_valid(self, form):
        # Calculate age based on date_of_birth
        if form.cleaned_data.get('date_of_birth'):
            from datetime import date
            dob = form.cleaned_data['date_of_birth']
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            form.instance.age = age

    

        # Save the form
        self.object = form.save()

        if self.request.headers.get('HX-Request'):
            # Return the success message div from the same template
            context = {
                'patient': self.object,
                'show_success': True
            }
            return render(self.request, self.template_name, context)
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get('HX-Request'):
            # Return the form with errors
            return render(self.request, self.template_name, {'form': form})
        return super().form_invalid(form)

class PatientUpdateView(LoginRequiredMixin, UpdateView):
    model = Patient  # Add this line
    template_name = 'patients/patient_form.html'
    success_url = reverse_lazy('patient_list')
    success_message = "Patient record updated successfully"
    fields = [
        'first_name', 'last_name', 'gender', 'phone_number', 'email',
        'date_of_birth', 'address', 'blood_type', 'allergies',
        'medical_conditions', 'medications', 'emergency_contact_name',
        'emergency_contact_phone'
    ]

class PatientDeleteView(LoginRequiredMixin, DeleteView):
    model = Patient
    template_name = 'patients/patient_delete_modal.html'
    success_url = reverse_lazy('patients:patient_list')
    success_message = "Patient was deleted successfully."
    

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)    