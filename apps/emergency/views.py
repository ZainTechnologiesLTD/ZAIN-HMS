from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.core.mixins import RequireHospitalSelectionMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
from django.contrib import messages
from .models import EmergencyCase, EmergencyMedication
from apps.core.mixins import require_hospital_selection
from .forms import EmergencyCaseForm, EmergencyTreatmentForm
# from tenants.permissions import  # Temporarily commented TenantFilterMixin

class EmergencyDashboardView(LoginRequiredMixin, ListView):
    template_name = 'emergency/case_dashboard.html'
    context_object_name = 'cases'
    
    def get_queryset(self):
        # Check if user has tenant assignment
        tenant = getattr(self.request.user, 'tenant', None) if hasattr(self.request, 'user') else None
        if not tenant:
            # If no tenant, return empty queryset
            return EmergencyCase.objects.none()
        
        # For now, since EmergencyCase doesn't have tenant field, return all cases
        # TODO: Add tenant field to EmergencyCase model in future migration
        return EmergencyCase.objects.exclude(status='discharged').order_by('priority', '-arrival_time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        context['critical_count'] = queryset.filter(priority='critical').count()
        context['waiting_count'] = queryset.filter(status='waiting').count()
        context['in_treatment_count'] = queryset.filter(status='in_treatment').count()
        return context

class EmergencyCaseCreateView(RequireHospitalSelectionMixin, LoginRequiredMixin, CreateView):
    model = EmergencyCase
    form_class = EmergencyCaseForm
    template_name = 'emergency/case_form.html'
    success_url = reverse_lazy('emergency:dashboard')

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.htmx:
            context = {'case': self.object}
            html = render_to_string('emergency/partials/case_card.html', context, request=self.request)
            return JsonResponse({
                'html': html,
                'message': 'Emergency case created successfully'
            })
        messages.success(self.request, 'Emergency case created successfully')
        return response

class EmergencyCaseUpdateView(LoginRequiredMixin, UpdateView):
    model = EmergencyCase
    form_class = EmergencyCaseForm
    template_name = 'emergency/case_form.html'
    success_url = reverse_lazy('emergency:dashboard')

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.htmx:
            context = {'case': self.object}
            html = render_to_string('emergency/partials/case_card.html', context, request=self.request)
            return JsonResponse({
                'html': html,
                'message': 'Emergency case updated successfully'
            })
        messages.success(self.request, 'Emergency case updated successfully')
        return response

class EmergencyCaseDetailView(LoginRequiredMixin, DetailView):
    model = EmergencyCase
    template_name = 'emergency/case_detail.html'
    context_object_name = 'case'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['treatment_form'] = EmergencyTreatmentForm()
        return context

@require_hospital_selection
def add_treatment(request, case_id):
    if not request.htmx:
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    case = get_object_or_404(EmergencyCase, id=case_id)
    form = EmergencyTreatmentForm(request.POST)
    
    if form.is_valid():
        treatment = form.save(commit=False)
        treatment.case = case
        treatment.performed_by = request.user
        treatment.save()
        
        context = {'treatment': treatment}
        html = render_to_string('emergency/partials/treatment_item.html', context, request=request)
        return JsonResponse({
            'html': html,
            'message': 'Treatment added successfully'
        })
    
    return JsonResponse({'error': form.errors}, status=400)