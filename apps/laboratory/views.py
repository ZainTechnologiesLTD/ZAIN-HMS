# apps/laboratory/views.py
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

# from tenants.permissions import  # Temporarily commented TenantFilterMixin
from apps.accounts.services import UserManagementService
from apps.core.mixins import RequireHospitalSelectionMixin

from .models import LabTest, LabOrder, LabOrderItem, LabResult, TestCategory
from .forms import (
    LabTestForm, LabOrderForm, LabOrderItemForm, LabResultForm, 
    TestCategoryForm, SampleCollectionForm
)
from apps.patients.models import Patient
from apps.doctors.models import Doctor


# Test Definition Views
class LabTestListView(ListView):  # TenantFilterMixin temporarily commented:
    model = LabTest
    template_name = 'laboratory/lab_test_list.html'
    context_object_name = 'lab_tests'
    paginate_by = 20
    required_permissions = ['laboratory.view_labtest']
    tenant_filter_field = 'tenant'

    def get_queryset(self):
        queryset = super().get_queryset()
        # Tenant filtering disabled; return base queryset
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search) |
                models.Q(test_code__icontains=search) |
                models.Q(description__icontains=search)
            )
        
        # Category filter
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
            
        return queryset.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Tenant disabled: show all active categories
        context['categories'] = TestCategory.objects.filter(is_active=True)
        context['search'] = self.request.GET.get('search', '')
        context['selected_category'] = self.request.GET.get('category', '')
        return context


class LabTestCreateView(RequireHospitalSelectionMixin, CreateView):
    model = LabTest
    form_class = LabTestForm
    template_name = 'laboratory/lab_test_create.html'
    success_url = reverse_lazy('laboratory:lab_test_list')
    required_permissions = ['laboratory.add_labtest']

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
    # Tenant not in use; do not pass it to the form
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f'Lab test "{form.instance.name}" created successfully.')
        return super().form_valid(form)


class LabTestDetailView(DetailView):  # TenantFilterMixin temporarily commented:
    model = LabTest
    template_name = 'laboratory/lab_test_detail.html'
    context_object_name = 'lab_test'
    required_permissions = ['laboratory.view_labtest']
    tenant_filter_field = 'tenant'


class LabTestUpdateView(UpdateView):  # TenantFilterMixin temporarily commented:
    model = LabTest
    form_class = LabTestForm
    template_name = 'laboratory/lab_test_update.html'
    success_url = reverse_lazy('laboratory:lab_test_list')
    required_permissions = ['laboratory.change_labtest']
    tenant_filter_field = 'tenant'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
    # Tenant not in use; do not pass it to the form
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, f'Lab test "{form.instance.name}" updated successfully.')
        return super().form_valid(form)


class LabTestDeleteView(DeleteView):  # TenantFilterMixin temporarily commented:
    model = LabTest
    template_name = 'laboratory/lab_test_delete.html'
    success_url = reverse_lazy('laboratory:lab_test_list')
    required_permissions = ['laboratory.delete_labtest']
    tenant_filter_field = 'tenant'

    def delete(self, request, *args, **kwargs):
        test = self.get_object()
        test_name = test.name
        messages.success(request, f'Lab test "{test_name}" deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Test Category Views
class TestCategoryListView(ListView):  # TenantFilterMixin temporarily commented:
    model = TestCategory
    template_name = 'laboratory/test_category_list.html'
    context_object_name = 'categories'
    required_permissions = ['laboratory.view_testcategory']
    tenant_filter_field = 'tenant'


class TestCategoryCreateView(RequireHospitalSelectionMixin, CreateView):
    model = TestCategory
    form_class = TestCategoryForm
    template_name = 'laboratory/test_category_create.html'
    success_url = reverse_lazy('laboratory:test_category_list')
    required_permissions = ['laboratory.add_testcategory']

    def form_valid(self, form):
        messages.success(self.request, f'Test category "{form.instance.name}" created successfully.')
        return super().form_valid(form)


# Lab Order Views
class LabOrderListView(ListView):  # TenantFilterMixin temporarily commented:
    model = LabOrder
    template_name = 'laboratory/lab_order_list.html'
    context_object_name = 'lab_orders'
    paginate_by = 20
    required_permissions = ['laboratory.view_laborder']
    tenant_filter_field = 'tenant'

    def get_queryset(self):
        queryset = super().get_queryset()
        # Tenant filtering disabled; return base queryset
        
        # Status filter
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        # Date range filter
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            queryset = queryset.filter(order_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(order_date__lte=date_to)
            
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = LabOrder.STATUS_CHOICES
        return context


class LabOrderCreateView(RequireHospitalSelectionMixin, CreateView):
    model = LabOrder
    form_class = LabOrderForm
    template_name = 'laboratory/lab_order_create.html'
    required_permissions = ['laboratory.add_laborder']

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
    # Tenant not in use; do not pass it to the form
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Show all active lab tests
        context['lab_tests'] = LabTest.objects.filter(is_active=True).order_by('name')
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Lab order created successfully.')
        with transaction.atomic():
            order = form.save()
            
            # Add selected tests to order
            selected_tests = self.request.POST.getlist('selected_tests')
            total_amount = 0
            
            for test_id in selected_tests:
                test = LabTest.objects.get(id=test_id)
                LabOrderItem.objects.create(
                    order=order,
                    test=test,
                    price=test.price
                )
                total_amount += test.price
            
            order.total_amount = total_amount
            order.net_amount = total_amount
            order.save()
            
        messages.success(self.request, f'Lab order "{order.order_number}" created successfully.')
        return redirect('laboratory:lab_order_detail', pk=order.pk)


class LabOrderDetailView(DetailView):  # TenantFilterMixin temporarily commented:
    model = LabOrder
    template_name = 'laboratory/lab_order_detail.html'
    context_object_name = 'lab_order'
    required_permissions = ['laboratory.view_laborder']
    tenant_filter_field = 'tenant'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order_items'] = LabOrderItem.objects.filter(order=self.object)
        return context


class LabOrderUpdateView(UpdateView):  # TenantFilterMixin temporarily commented:
    model = LabOrder
    form_class = LabOrderForm
    template_name = 'laboratory/lab_order_update.html'
    required_permissions = ['laboratory.change_laborder']
    tenant_filter_field = 'tenant'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
    # Tenant not in use; do not pass it to the form
        return kwargs

    def get_success_url(self):
        return reverse('laboratory:lab_order_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, f'Lab order "{form.instance.order_number}" updated successfully.')
        return super().form_valid(form)


class LabOrderDeleteView(DeleteView):  # TenantFilterMixin temporarily commented:
    model = LabOrder
    template_name = 'laboratory/lab_order_delete.html'
    success_url = reverse_lazy('laboratory:lab_order_list')
    required_permissions = ['laboratory.delete_laborder']
    tenant_filter_field = 'tenant'

    def delete(self, request, *args, **kwargs):
        order = self.get_object()
        order_number = order.order_number
        messages.success(request, f'Lab order "{order_number}" deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Result Entry Views
class LabResultCreateView(RequireHospitalSelectionMixin, CreateView):
    model = LabResult
    form_class = LabResultForm
    template_name = 'laboratory/lab_result_create.html'
    required_permissions = ['laboratory.add_labresult']

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
    # Tenant not in use; do not pass it to the form
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_item_id = self.kwargs.get('order_item_id')
        context['order_item'] = get_object_or_404(LabOrderItem, id=order_item_id)
        return context

    def form_valid(self, form):
        order_item_id = self.kwargs.get('order_item_id')
        order_item = get_object_or_404(LabOrderItem, id=order_item_id)
        
        form.instance.order_item = order_item
        form.instance.performed_by = self.request.user
        
        messages.success(self.request, 'Lab result entered successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('laboratory:lab_order_detail', kwargs={'pk': self.object.order_item.order.pk})


class LabResultUpdateView(UpdateView):  # TenantFilterMixin temporarily commented:
    model = LabResult
    form_class = LabResultForm
    template_name = 'laboratory/lab_result_update.html'
    required_permissions = ['laboratory.change_labresult']
    tenant_filter_field = 'order_item__order__tenant'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
    # Tenant not in use; do not pass it to the form
        return kwargs

    def get_success_url(self):
        return reverse('laboratory:lab_order_detail', kwargs={'pk': self.object.order_item.order.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Lab result updated successfully.')
        return super().form_valid(form)


# Sample Collection
class SampleCollectionView(UpdateView):  # TenantFilterMixin temporarily commented:
    model = LabOrderItem
    form_class = SampleCollectionForm
    template_name = 'laboratory/sample_collection.html'
    required_permissions = ['laboratory.change_laborderitem']
    tenant_filter_field = 'order__tenant'

    def get_success_url(self):
        return reverse('laboratory:lab_order_detail', kwargs={'pk': self.object.order.pk})

    def form_valid(self, form):
        form.instance.collected_by = self.request.user
        form.instance.status = 'SAMPLE_COLLECTED'
        messages.success(self.request, 'Sample collection updated successfully.')
        return super().form_valid(form)


# Dashboard/Home view
@login_required
def laboratory_dashboard(request):
    """Laboratory module dashboard"""
    # Get laboratory statistics
    total_tests = LabTest.objects.filter(is_active=True).count()
    pending_orders = LabOrder.objects.filter(status__in=['ORDERED', 'SAMPLE_COLLECTED']).count()
    completed_today = LabOrder.objects.filter(
        status='COMPLETED',
        completed_at__date=timezone.now().date()
    ).count()
    # Recent orders
    recent_orders = LabOrder.objects.order_by('-order_date')[:10]
    
    context = {
        'total_tests': total_tests,
        'pending_orders': pending_orders,
        'completed_today': completed_today,
        'recent_orders': recent_orders,
    }
    
    return render(request, 'laboratory/dashboard.html', context)


# Legacy views for backward compatibility
def diagnostic_list(request):
    """Legacy view - redirect to new lab test list"""
    return redirect('laboratory:lab_test_list')

def lab_test_list(request):
    """Legacy view - redirect to new lab test list"""
    return redirect('laboratory:lab_test_list')