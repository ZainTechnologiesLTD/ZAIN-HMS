from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
from django.contrib import messages
from .models import EmergencyCase, EmergencyTreatment
from .forms import EmergencyCaseForm, EmergencyTreatmentForm

class EmergencyDashboardView(LoginRequiredMixin, ListView):
    template_name = 'emergency/dashboard.html'
    context_object_name = 'cases'
    
    def get_queryset(self):
        return EmergencyCase.objects.exclude(status='discharged').order_by('priority', '-arrival_time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['critical_count'] = self.get_queryset().filter(priority='critical').count()
        context['waiting_count'] = self.get_queryset().filter(status='waiting').count()
        context['in_treatment_count'] = self.get_queryset().filter(status='in_treatment').count()
        return context

class EmergencyCaseCreateView(LoginRequiredMixin, CreateView):
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