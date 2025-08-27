# apps/staff/views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from apps.accounts.models import CustomUser as User
from apps.accounts.services import UserManagementService
# from tenants.permissions import  # Temporarily commented TenantFilterMixin
from .models import StaffProfile
from .forms import StaffProfileForm, StaffSearchForm
from apps.core.mixins import RequireHospitalSelectionMixin


class StaffListView(ListView):  # TenantFilterMixin temporarily commented:
    model = StaffProfile
    template_name = 'staff/staff_list.html'
    context_object_name = 'staff_members'
    paginate_by = 20
    required_roles = ['admin', 'hr_manager', 'superadmin']
    tenant_filter_field = 'tenant'

    def get_queryset(self):
        # Use TenantFilterMixin to get tenant-filtered queryset
        queryset = self.filter_by_tenant(StaffProfile.objects.filter(is_active=True)).select_related('user', 'department')
        
        # Search functionality
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(position_title__icontains=search) |
                Q(staff_id__icontains=search) |
                Q(email__icontains=search) |
                Q(phone_number__icontains=search) |
                Q(department__name__icontains=search)
            )
        
        # Filter by role/position
        role = self.request.GET.get('role')
        if role:
            if role == 'NO_USER':
                queryset = queryset.filter(user__isnull=True)
            else:
                queryset = queryset.filter(user__role=role)
        
        # Filter by department
        department = self.request.GET.get('department')
        if department:
            queryset = queryset.filter(department_id=department)
            
        return queryset.order_by('first_name', 'last_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = StaffSearchForm(self.request.GET)
        
        # Use the filtered queryset for counts
        base_queryset = self.filter_by_tenant(StaffProfile.objects.filter(is_active=True))
        context['total_staff'] = base_queryset.count()
        context['staff_without_users'] = base_queryset.filter(user__isnull=True).count()
        
        # Role distribution
        context['role_distribution'] = {}
        for role_code, role_name in User.ROLE_CHOICES:
            if role_code not in ['PATIENT', 'DOCTOR']:  # Exclude non-staff roles
                count = base_queryset.filter(user__role=role_code).count()
                if count > 0:
                    context['role_distribution'][role_name] = count
        
        return context


class StaffDetailView(DetailView):  # TenantFilterMixin temporarily commented:
    model = StaffProfile
    template_name = 'staff/staff_detail.html'
    context_object_name = 'staff_member'
    required_roles = ['admin', 'hr_manager', 'superadmin']
    tenant_filter_field = 'tenant'
    
    def get_queryset(self):
        return self.filter_by_tenant(StaffProfile.objects.all())


class StaffCreateView(RequireHospitalSelectionMixin, CreateView):
    model = StaffProfile
    form_class = StaffProfileForm
    template_name = 'staff/staff_form.html'
    success_url = reverse_lazy('staff:staff_list')
    required_roles = ['admin', 'hr_manager', 'superadmin']
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.user.tenant
        return kwargs
    
    def form_valid(self, form):
        staff = form.save(commit=False)
        staff.tenant = self.request.user.tenant
        staff.created_by = self.request.user
        
        # Check if user account should be created
        create_user = form.cleaned_data.get('create_user_account', False)
        
        staff.save()
        
        if create_user:
            try:
                # Use UserManagementService to create user account
                user = UserManagementService.create_user_for_existing_staff(
                    staff_profile_id=staff.id,
                    created_by_user=self.request.user
                )
                
                messages.success(
                    self.request,
                    f'Staff member {staff.get_full_name()} created successfully! '
                    f'Login credentials have been sent to {staff.email}.'
                )
            except Exception as e:
                messages.warning(
                    self.request,
                    f'Staff member created but failed to create user account: {str(e)}'
                )
        else:
            messages.success(self.request, f'Staff member {staff.get_full_name()} created successfully.')
        
        return super().form_valid(form)


class StaffUpdateView(UpdateView):  # TenantFilterMixin temporarily commented:
    model = StaffProfile
    form_class = StaffProfileForm
    template_name = 'staff/staff_form.html'
    success_url = reverse_lazy('staff:staff_list')
    required_roles = ['admin', 'hr_manager', 'superadmin']
    tenant_filter_field = 'tenant'
    
    def get_queryset(self):
        return self.filter_by_tenant(StaffProfile.objects.all())
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.user.tenant
        return kwargs
    
    def form_valid(self, form):
        staff = form.save()
        
        # Update the linked user's information if email or name changed
        if staff.user:
            user = staff.user
            user.email = staff.email
            user.first_name = staff.first_name
            user.last_name = staff.last_name
            user.middle_name = staff.middle_name
            user.phone = staff.phone_number
            user.save()
        
        messages.success(self.request, 'Staff profile updated successfully!')
        return super().form_valid(form)


class CreateUserForStaffView(View):
    """Create a user account for an existing staff member"""
    required_roles = ['admin', 'hr_manager', 'superadmin']
    
    def post(self, request, pk):
        try:
            staff = get_object_or_404(StaffProfile, pk=pk)
            
            # Check if staff already has a user
            if staff.user:
                messages.warning(request, f'Staff member {staff.get_full_name()} already has a user account.')
                return redirect('staff:staff_detail', pk=pk)
            
            # Create user account for the staff
            user = UserManagementService.create_user_for_existing_staff(
                staff_profile_id=staff.id,
                created_by_user=request.user
            )
            
            messages.success(
                request,
                f'User account created successfully for {staff.get_full_name()}! '
                f'Login credentials have been sent to {staff.email}.'
            )
            
        except Exception as e:
            messages.error(request, f'Error creating user account: {str(e)}')
        
        return redirect('staff:staff_detail', pk=pk)


class LinkStaffUserView(View):
    """Link an existing user to an existing staff member"""
    required_roles = ['admin', 'hr_manager', 'superadmin']
    
    def get(self, request, pk):
        staff = get_object_or_404(StaffProfile, pk=pk)
        
        # Check if staff already has a user
        if staff.user:
            messages.warning(request, f'Staff member {staff.get_full_name()} already has a linked user account.')
            return redirect('staff:staff_detail', pk=pk)
        
        # Get available users (non-patient roles without linked staff/doctor)
        available_users = User.objects.filter(
            role__in=['NURSE', 'PHARMACIST', 'LAB_TECHNICIAN', 'RADIOLOGIST', 'ACCOUNTANT', 'HR_MANAGER', 'RECEPTIONIST', 'STAFF'],
            tenant=request.user.tenant,
            staff_profile__isnull=True,  # Users not already linked to a staff
            doctor__isnull=True  # Users not linked to a doctor
        ).order_by('first_name', 'last_name')
        
        context = {
            'staff_member': staff,
            'available_users': available_users
        }
        
        return render(request, 'staff/link_user.html', context)
    
    def post(self, request, pk):
        try:
            staff = get_object_or_404(StaffProfile, pk=pk)
            user_id = request.POST.get('user_id')
            
            if not user_id:
                messages.error(request, 'Please select a user to link.')
                return redirect('staff:link_user', pk=pk)
            
            # Link the user to the staff
            UserManagementService.link_user_to_staff(
                user_id=user_id,
                staff_profile_id=staff.id,
                linked_by_user=request.user
            )
            
            messages.success(
                request,
                f'User successfully linked to {staff.get_full_name()}!'
            )
            
        except Exception as e:
            messages.error(request, f'Error linking user: {str(e)}')
        
        return redirect('staff:staff_detail', pk=pk)


@login_required
@require_POST
def unlink_staff_user(request, pk):
    """Unlink user from staff (AJAX endpoint)"""
    try:
        staff = get_object_or_404(StaffProfile, pk=pk)
        
        if not staff.user:
            return JsonResponse({'success': False, 'error': 'Staff has no linked user account.'})
        
        # Check permissions
        if not (request.user.role in ['ADMIN', 'SUPERADMIN', 'HR_MANAGER'] or request.user.is_superuser):
            return JsonResponse({'success': False, 'error': 'Permission denied.'})
        
        user_name = staff.user.get_full_name()
        
        # Unlink
        staff.user = None
        staff.save()
        
        return JsonResponse({
            'success': True,
            'message': f'User {user_name} has been unlinked from {staff.get_full_name()}'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


class StaffWithoutUsersView(ListView):  # TenantFilterMixin temporarily commented:
    """List staff who don't have user accounts"""
    model = StaffProfile
    template_name = 'staff/staff_without_users.html'
    context_object_name = 'staff_members'
    paginate_by = 20
    required_roles = ['admin', 'hr_manager', 'superadmin']
    tenant_filter_field = 'tenant'
    
    def get_queryset(self):
        # Get staff without user accounts
        return self.filter_by_tenant(StaffProfile.objects.filter(
            user__isnull=True,
            is_active=True
        )).order_by('first_name', 'last_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_staff_without_users'] = self.get_queryset().count()
        return context


class StaffByRoleView(ListView):  # TenantFilterMixin temporarily commented:
    """List staff by specific role"""
    model = StaffProfile
    template_name = 'staff/staff_by_role.html'
    context_object_name = 'staff_members'
    paginate_by = 20
    required_roles = ['admin', 'hr_manager', 'superadmin']
    tenant_filter_field = 'tenant'
    
    def get_queryset(self):
        role = self.kwargs.get('role')
        if role == 'NO_USER':
            return self.filter_by_tenant(StaffProfile.objects.filter(
                user__isnull=True,
                is_active=True
            )).order_by('first_name', 'last_name')
        else:
            return self.filter_by_tenant(StaffProfile.objects.filter(
                user__role=role,
                is_active=True
            )).select_related('user').order_by('first_name', 'last_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        role = self.kwargs.get('role')
        
        if role == 'NO_USER':
            context['role_name'] = 'Staff Without User Accounts'
        else:
            role_dict = dict(User.ROLE_CHOICES)
            context['role_name'] = role_dict.get(role, role)
        
        context['role_code'] = role
        context['total_count'] = self.get_queryset().count()
        return context
