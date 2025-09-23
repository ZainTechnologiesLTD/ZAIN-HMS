# apps/radiology/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.db import transaction
from django.db import models
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.contrib.auth.mixins import LoginRequiredMixin

# ZAIN HMS unified system mixins
from apps.core.mixins import UnifiedSystemMixin

# from apps.accounts.services import UserManagementService

from .models import StudyType, RadiologyOrder, RadiologyOrderItem, ImagingStudy, RadiologyEquipment
from .forms import (
    StudyTypeForm, RadiologyOrderForm, RadiologyOrderItemForm, 
    ImagingStudyForm, RadiologyEquipmentForm, RadiologistReportForm
)
from apps.patients.models import Patient
from apps.doctors.models import Doctor


# Dashboard View
class RadiologyDashboardView(UnifiedSystemMixin, ListView):  # TenantFilterMixin temporarily commented:
    model = RadiologyOrder
    template_name = 'radiology/dashboard.html'
    context_object_name = 'recent_orders'
    paginate_by = 10
    required_permissions = ['radiology.view_radiologyorder']
    # tenant_filter_field removed for unified single-DB mode

    def get_queryset(self):
        try:
            # Check if the table exists before trying to query
            from django.db import connection
            table_names = connection.introspection.table_names()
            if 'radiology_radiologyorder' not in table_names:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning("RadiologyOrder table does not exist, returning empty queryset")
                # Create an empty queryset without hitting the database
                return self.model.objects.none()
            
            queryset = super().get_queryset()
            queryset = self.filter_by_tenant(queryset)
            return queryset.select_related('patient', 'ordering_doctor').order_by('-created_at')
        except Exception as e:
            # Handle case where radiology tables don't exist
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error accessing radiology data: {e}")
            # Return empty queryset to prevent crashes
            return self.model.objects.none()

    def get_context_data(self, **kwargs):
        try:
            # Check if tables exist before querying
            from django.db import connection
            table_names = connection.introspection.table_names()
            
            if 'radiology_radiologyorder' not in table_names:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning("Radiology tables do not exist, using empty context")
                
                # Set object_list to empty for ListView to work properly
                if not hasattr(self, 'object_list'):
                    self.object_list = self.get_queryset()
                
                # Return minimal context to prevent crashes
                context = super().get_context_data(**kwargs)
                context.update({
                    'total_orders_today': 0,
                    'pending_orders': 0,
                    'completed_studies': 0,
                    'equipment_count': 0,
                })
                return context
            
            context = super().get_context_data(**kwargs)
            
            # Get statistics for the tenant
            today = timezone.now().date()
            tenant_orders = self.filter_by_tenant(RadiologyOrder.objects.all())
            tenant_equipment = self.filter_by_tenant(RadiologyEquipment.objects.all())
            
            context.update({
                'total_orders_today': tenant_orders.filter(created_at__date=today).count(),
                'pending_orders': tenant_orders.filter(status='pending').count(),
                'completed_studies': tenant_orders.filter(status='completed').count(),
                'equipment_count': tenant_equipment.filter(status='active').count(),
            })
            
            return context
        except Exception as e:
            # Handle case where radiology tables don't exist
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error getting radiology context data: {e}")
            
            # Set object_list to empty for ListView to work properly
            if not hasattr(self, 'object_list'):
                self.object_list = self.get_queryset()
            
            # Return minimal context to prevent crashes
            context = super().get_context_data(**kwargs)
            context.update({
                'total_orders_today': 0,
                'pending_orders': 0,
                'completed_studies': 0,
                'equipment_count': 0,
            })
            return context


# Study Type Views
class StudyTypeListView(UnifiedSystemMixin, ListView):  # TenantFilterMixin temporarily commented:
    model = StudyType
    template_name = 'radiology/study_type_list.html'
    context_object_name = 'study_types'
    paginate_by = 20
    required_permissions = ['radiology.view_studytype']
    # tenant_filter_field removed for unified single-DB mode

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = self.filter_by_tenant(queryset)
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search) |
                models.Q(code__icontains=search) |
                models.Q(description__icontains=search)
            )
        
        # Modality filter
        modality = self.request.GET.get('modality')
        if modality:
            queryset = queryset.filter(modality=modality)
            
        return queryset.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['modalities'] = StudyType.MODALITY_CHOICES
        return context


class StudyTypeCreateView(UnifiedSystemMixin, CreateView):
    model = StudyType
    form_class = StudyTypeForm
    template_name = 'radiology/study_type_form.html'
    success_url = reverse_lazy('radiology:study_type_list')
    required_permissions = ['radiology.add_studytype']

    def form_valid(self, form):
        form.instance.tenant = self.request.user.hospital
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Study type created successfully.')
        return super().form_valid(form)


class StudyTypeDetailView(UnifiedSystemMixin, DetailView):  # TenantFilterMixin temporarily commented:
    model = StudyType
    template_name = 'radiology/study_type_detail.html'
    context_object_name = 'study_type'
    required_permissions = ['radiology.view_studytype']
    # tenant_filter_field removed for unified single-DB mode

    def get_queryset(self):
        queryset = super().get_queryset()
        return self.filter_by_tenant(queryset)


class StudyTypeUpdateView(UnifiedSystemMixin, UpdateView):  # TenantFilterMixin temporarily commented:
    model = StudyType
    form_class = StudyTypeForm
    template_name = 'radiology/study_type_form.html'
    required_permissions = ['radiology.change_studytype']
    # tenant_filter_field removed for unified single-DB mode

    def get_queryset(self):
        queryset = super().get_queryset()
        return self.filter_by_tenant(queryset)

    def get_success_url(self):
        return reverse('radiology:study_type_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Study type updated successfully.')
        return super().form_valid(form)


class StudyTypeDeleteView(UnifiedSystemMixin, DeleteView):  # TenantFilterMixin temporarily commented:
    model = StudyType
    template_name = 'radiology/study_type_confirm_delete.html'
    success_url = reverse_lazy('radiology:study_type_list')
    required_permissions = ['radiology.delete_studytype']
    # tenant_filter_field removed for unified single-DB mode

    def get_queryset(self):
        queryset = super().get_queryset()
        return self.filter_by_tenant(queryset)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Study type deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Radiology Order Views
class RadiologyOrderListView(UnifiedSystemMixin, ListView):  # TenantFilterMixin temporarily commented:
    model = RadiologyOrder
    template_name = 'radiology/order_list.html'
    context_object_name = 'orders'
    paginate_by = 20
    required_permissions = ['radiology.view_radiologyorder']
    # tenant_filter_field removed for unified single-DB mode

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = self.filter_by_tenant(queryset)
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(order_number__icontains=search) |
                models.Q(patient__patient_id__icontains=search) |
                models.Q(patient__first_name__icontains=search) |
                models.Q(patient__last_name__icontains=search) |
                models.Q(ordering_doctor__first_name__icontains=search) |
                models.Q(ordering_doctor__last_name__icontains=search)
            )
        
        # Status filter
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        # Priority filter  
        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
            
        return queryset.select_related('patient', 'ordering_doctor').prefetch_related('items__study_type').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'status_choices': RadiologyOrder.STATUS_CHOICES,
            'priority_choices': RadiologyOrder.PRIORITY_CHOICES,
        })
        return context


class RadiologyOrderCreateView(UnifiedSystemMixin, CreateView):
    model = RadiologyOrder
    form_class = RadiologyOrderForm
    template_name = 'radiology/order_form.html'
    success_url = reverse_lazy('radiology:order_list')
    required_permissions = ['radiology.add_radiologyorder']

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.user.hospital
        return kwargs

    def form_valid(self, form):
        form.instance.tenant = self.request.user.hospital
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Radiology order created successfully.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Handle users without tenant (graceful degradation)
        tenant = self.request.user.hospital
        if tenant:
            context['study_types'] = StudyType.objects.filter(
                tenant=tenant,
                is_active=True
            ).order_by('name')
        else:
            # No tenant - provide empty list to prevent database errors
            context['study_types'] = []
            
        return context


class RadiologyOrderDetailView(UnifiedSystemMixin, DetailView):  # TenantFilterMixin temporarily commented:
    model = RadiologyOrder
    template_name = 'radiology/order_detail.html'
    context_object_name = 'order'
    required_permissions = ['radiology.view_radiologyorder']
    # tenant_filter_field removed for unified single-DB mode

    def get_queryset(self):
        queryset = super().get_queryset()
        return self.filter_by_tenant(queryset).prefetch_related(
            'items__study_type', 
            'items__study'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order_items'] = self.object.items.all()
        # Get imaging studies through the order items
        imaging_studies = []
        for item in self.object.items.all():
            if hasattr(item, 'study') and item.study:
                imaging_studies.append(item.study)
        context['imaging_studies'] = imaging_studies
        return context


class RadiologyOrderUpdateView(UnifiedSystemMixin, UpdateView):  # TenantFilterMixin temporarily commented:
    model = RadiologyOrder
    form_class = RadiologyOrderForm
    template_name = 'radiology/order_form.html'
    required_permissions = ['radiology.change_radiologyorder']
    # tenant_filter_field removed for unified single-DB mode

    def get_queryset(self):
        queryset = super().get_queryset()
        return self.filter_by_tenant(queryset)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.user.hospital
        return kwargs

    def get_success_url(self):
        return reverse('radiology:order_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Radiology order updated successfully.')
        return super().form_valid(form)


class RadiologyOrderDeleteView(UnifiedSystemMixin, DeleteView):  # TenantFilterMixin temporarily commented:
    model = RadiologyOrder
    template_name = 'radiology/order_confirm_delete.html'
    success_url = reverse_lazy('radiology:order_list')
    required_permissions = ['radiology.delete_radiologyorder']
    # tenant_filter_field removed for unified single-DB mode

    def get_queryset(self):
        queryset = super().get_queryset()
        return self.filter_by_tenant(queryset)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Radiology order deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Imaging Study Views
class ImagingStudyListView(ListView):  # TenantFilterMixin temporarily commented:
    model = ImagingStudy
    template_name = 'radiology/study_list.html'
    context_object_name = 'studies'
    paginate_by = 20
    required_permissions = ['radiology.view_imagingstudy']
    # tenant_filter_field removed for unified single-DB mode

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = self.filter_by_tenant(queryset)
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(study_instance_uid__icontains=search) |
                models.Q(order_item__order__patient__patient_id__icontains=search) |
                models.Q(order_item__order__patient__first_name__icontains=search) |
                models.Q(order_item__order__patient__last_name__icontains=search)
            )
            
        return queryset.select_related('order_item__order__patient', 'reported_by', 'reviewed_by').order_by('-study_date')


class ImagingStudyCreateView(UnifiedSystemMixin, CreateView):
    model = ImagingStudy
    form_class = ImagingStudyForm
    template_name = 'radiology/study_form.html'
    success_url = reverse_lazy('radiology:study_list')
    required_permissions = ['radiology.add_imagingstudy']

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.user.hospital
        return kwargs

    def form_valid(self, form):
        form.instance.performed_by = self.request.user
        messages.success(self.request, 'Imaging study created successfully.')
        return super().form_valid(form)


class ImagingStudyDetailView(DetailView):  # TenantFilterMixin temporarily commented:
    model = ImagingStudy
    template_name = 'radiology/study_detail.html'
    context_object_name = 'study'
    required_permissions = ['radiology.view_imagingstudy']
    # tenant_filter_field removed for unified single-DB mode

    def get_queryset(self):
        queryset = super().get_queryset()
        return self.filter_by_tenant(queryset).prefetch_related('images')


class ImagingStudyUpdateView(UpdateView):  # TenantFilterMixin temporarily commented:
    model = ImagingStudy
    form_class = ImagingStudyForm
    template_name = 'radiology/study_form.html'
    required_permissions = ['radiology.change_imagingstudy']
    # tenant_filter_field removed for unified single-DB mode

    def get_queryset(self):
        queryset = super().get_queryset()
        return self.filter_by_tenant(queryset)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.user.hospital
        return kwargs

    def get_success_url(self):
        return reverse('radiology:study_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Imaging study updated successfully.')
        return super().form_valid(form)


class RadiologistReportView(UpdateView):  # TenantFilterMixin temporarily commented:
    model = ImagingStudy
    form_class = RadiologistReportForm
    template_name = 'radiology/radiologist_report.html'
    required_permissions = ['radiology.change_imagingstudy']
    # tenant_filter_field removed for unified single-DB mode

    def get_queryset(self):
        queryset = super().get_queryset()
        return self.filter_by_tenant(queryset)

    def get_success_url(self):
        return reverse('radiology:study_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.radiologist = self.request.user
        form.instance.report_date = timezone.now()
        form.instance.status = 'reported'
        messages.success(self.request, 'Radiologist report submitted successfully.')
        return super().form_valid(form)


# Equipment Views
class RadiologyEquipmentListView(ListView):  # TenantFilterMixin temporarily commented:
    model = RadiologyEquipment
    template_name = 'radiology/equipment_list.html'
    context_object_name = 'equipment'
    paginate_by = 20
    required_permissions = ['radiology.view_radiologyequipment']
    # tenant_filter_field removed for unified single-DB mode

    def get_queryset(self):
        queryset = super().get_queryset()
        return self.filter_by_tenant(queryset)


class RadiologyEquipmentCreateView(UnifiedSystemMixin, CreateView):
    model = RadiologyEquipment
    form_class = RadiologyEquipmentForm
    template_name = 'radiology/equipment_form.html'
    success_url = reverse_lazy('radiology:equipment_list')
    required_permissions = ['radiology.add_radiologyequipment']

    def form_valid(self, form):
        form.instance.tenant = self.request.user.hospital
        messages.success(self.request, 'Equipment created successfully.')
        return super().form_valid(form)


class RadiologyEquipmentDetailView(DetailView):  # TenantFilterMixin temporarily commented:
    model = RadiologyEquipment
    template_name = 'radiology/equipment_detail.html'
    context_object_name = 'equipment_item'
    required_permissions = ['radiology.view_radiologyequipment']
    # tenant_filter_field removed for unified single-DB mode

    def get_queryset(self):
        queryset = super().get_queryset()
        return self.filter_by_tenant(queryset)


class RadiologyEquipmentUpdateView(UpdateView):  # TenantFilterMixin temporarily commented:
    model = RadiologyEquipment
    form_class = RadiologyEquipmentForm
    template_name = 'radiology/equipment_form.html'
    required_permissions = ['radiology.change_radiologyequipment']
    # tenant_filter_field removed for unified single-DB mode

    def get_queryset(self):
        queryset = super().get_queryset()
        return self.filter_by_tenant(queryset)

    def get_success_url(self):
        return reverse('radiology:equipment_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Equipment updated successfully.')
        return super().form_valid(form)


class RadiologyEquipmentDeleteView(DeleteView):  # TenantFilterMixin temporarily commented:
    model = RadiologyEquipment
    template_name = 'radiology/equipment_confirm_delete.html'
    success_url = reverse_lazy('radiology:equipment_list')
    required_permissions = ['radiology.delete_radiologyequipment']
    # tenant_filter_field removed for unified single-DB mode

    def get_queryset(self):
        queryset = super().get_queryset()
        return self.filter_by_tenant(queryset)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Equipment deleted successfully.')
        return super().delete(request, *args, **kwargs)


# API Views for AJAX calls
class PatientSearchAPIView(ListView):  # TenantFilterMixin temporarily commented:
    model = Patient
    required_permissions = ['radiology.view_radiologyorder']
    # tenant_filter_field removed for unified single-DB mode

    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '')
        if len(query) < 2:
            return JsonResponse({'results': []})
            
        patients = self.filter_by_tenant(Patient.objects.all()).filter(
            models.Q(patient_id__icontains=query) |
            models.Q(first_name__icontains=query) |
            models.Q(last_name__icontains=query)
        )[:10]
        
        results = []
        for patient in patients:
            results.append({
                'id': patient.id,
                'text': f"{patient.patient_id} - {patient.get_full_name()}",
                'patient_id': patient.patient_id,
                'name': patient.get_full_name()
            })
            
        return JsonResponse({'results': results})


class StudyTypeAPIView(ListView):  # TenantFilterMixin temporarily commented:
    model = StudyType
    required_permissions = ['radiology.view_studytype']
    # tenant_filter_field removed for unified single-DB mode

    def get(self, request, *args, **kwargs):
        study_types = self.filter_by_tenant(StudyType.objects.all()).filter(is_active=True)
        
        results = []
        for study_type in study_types:
            results.append({
                'id': study_type.id,
                'name': study_type.name,
                'code': study_type.code,
                'price': str(study_type.price),
                'modality': study_type.modality
            })
            
        return JsonResponse({'results': results})
