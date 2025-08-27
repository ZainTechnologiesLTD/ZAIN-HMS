from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q
# from tenants.permissions import  # Temporarily commented TenantFilterMixin
from apps.accounts.services import UserManagementService
from .forms import NurseForm, NurseScheduleForm, NurseLeaveForm
from apps.staff.models import Department
from .models import Nurse, NurseSchedule, NurseLeave
from apps.core.mixins import RequireHospitalSelectionMixin

class NurseListView(LoginRequiredMixin, ListView):  # TenantFilterMixin removed; router handles tenant DB
    model = Nurse
    template_name = 'nurses/nurse_list.html'
    context_object_name = 'nurses'
    paginate_by = 10
    required_roles = ['admin', 'hr_manager', 'doctor', 'nurse']

    def get_queryset(self):
        # Tenant isolation is enforced by the DB router using hospital context
        queryset = Nurse.objects.all()
        department = self.request.GET.get('department')
        shift = self.request.GET.get('shift')
        search = self.request.GET.get('search')

        if department:
            queryset = queryset.filter(department__id=department)
        if shift:
            queryset = queryset.filter(shift=shift)
        if search:
            # Avoid user__ lookups to prevent cross-database queries
            queryset = queryset.filter(
                Q(employee_id__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Departments live in the same tenant DB; no explicit tenant FK
        try:
            # Try to load departments and force evaluation; if table is missing, fall back gracefully
            context['departments'] = list(Department.objects.all())
        except Exception:
            context['departments'] = []
        return context

class NurseDetailView(LoginRequiredMixin, DetailView):
    model = Nurse
    template_name = 'nurses/nurse_detail.html'
    context_object_name = 'nurse'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['schedules'] = self.object.schedules.all()[:5]
        context['leaves'] = self.object.leaves.all()[:5]
        return context

class NurseCreateView(RequireHospitalSelectionMixin, LoginRequiredMixin, CreateView):
    model = Nurse
    form_class = NurseForm
    template_name = 'nurses/nurse_form.html'
    success_url = reverse_lazy('nurses:nurse_list')
    required_roles = ['admin', 'hr_manager']

    def form_valid(self, form):
        try:
            nurse = form.save(commit=False)
            
            # Use UserManagementService to create user account
            user = UserManagementService.create_user_account(
                email=getattr(nurse, 'email', ''),
                first_name=getattr(nurse, 'first_name', ''),
                last_name=getattr(nurse, 'last_name', ''),
                role='NURSE',
                created_by=self.request.user,
                additional_data={
                    'employee_id': getattr(nurse, 'employee_id', ''),
                    'phone': getattr(nurse, 'phone', ''),
                    'department': nurse.department.name if nurse.department else None,
                    'shift': getattr(nurse, 'shift', ''),
                    'qualification': getattr(nurse, 'qualification', ''),
                }
            )
            
            # Link the nurse to the created user
            nurse.user = user
            nurse.save()
            
            messages.success(
                self.request,
                f'Nurse {nurse.get_full_name()} created successfully! '
                f'Login credentials have been sent to {nurse.email}.'
            )
            
            return super().form_valid(form)
            
        except Exception as e:
            messages.error(
                self.request,
                f'Error creating nurse account: {str(e)}'
            )
            return self.form_invalid(form)

class NurseUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Nurse
    form_class = NurseForm
    template_name = 'nurses/nurse_form.html'
    success_url = reverse_lazy('nurses:nurse_list')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        messages.success(self.request, 'Nurse profile updated successfully!')
        return super().form_valid(form)

class NurseDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Nurse
    template_name = 'nurses/nurse_confirm_delete.html'
    success_url = reverse_lazy('nurses:nurse_list')

    def test_func(self):
        return self.request.user.is_staff

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Nurse profile deleted successfully!')
        return super().delete(request, *args, **kwargs)

# Schedule Views
class ScheduleCreateView(RequireHospitalSelectionMixin, LoginRequiredMixin, CreateView):
    model = NurseSchedule
    form_class = NurseScheduleForm
    template_name = 'nurses/schedule_form.html'

    def form_valid(self, form):
        form.instance.nurse_id = self.kwargs['nurse_id']
        messages.success(self.request, 'Schedule created successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('nurses:nurse_detail', kwargs={'pk': self.kwargs['nurse_id']})

class ScheduleUpdateView(LoginRequiredMixin, UpdateView):
    model = NurseSchedule
    form_class = NurseScheduleForm
    template_name = 'nurses/schedule_form.html'

    def get_success_url(self):
        return reverse_lazy('nurses:nurse_detail', kwargs={'pk': self.object.nurse.id})

# Leave Management Views
@login_required
def leave_request(request, nurse_id):
    nurse = get_object_or_404(Nurse, id=nurse_id)
    
    if request.method == 'POST':
        form = NurseLeaveForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.nurse = nurse
            leave.save()
            messages.success(request, 'Leave request submitted successfully!')
            return redirect('nurses:nurse_detail', pk=nurse_id)
    else:
        form = NurseLeaveForm()
    
    return render(request, 'nurses/leave_form.html', {'form': form, 'nurse': nurse})

@login_required
def approve_leave(request, leave_id):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to approve leaves!')
        return redirect('nurses:nurse_list')

    leave = get_object_or_404(NurseLeave, id=leave_id)
    leave.status = 'approved'
    leave.approved_by = request.user
    leave.save()
    messages.success(request, 'Leave approved successfully!')
    return redirect('nurses:nurse_detail', pk=leave.nurse.id)

@login_required
def reject_leave(request, leave_id):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to reject leaves!')
        return redirect('nurses:nurse_list')

    leave = get_object_or_404(NurseLeave, id=leave_id)
    leave.status = 'rejected'
    leave.approved_by = request.user
    leave.save()
    messages.success(request, 'Leave rejected successfully!')
    return redirect('nurses:nurse_detail', pk=leave.nurse.id)