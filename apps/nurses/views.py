from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import JsonResponse
# from apps.accounts.services import UserManagementService
from .forms import NurseForm, NurseScheduleForm, NurseLeaveForm
from apps.staff.models import Department
from .models import Nurse, NurseSchedule, NurseLeave
from apps.core.mixins import UnifiedSystemMixin

class NurseListView(LoginRequiredMixin, ListView):  # TenantFilterMixin removed; router handles tenant DB
    model = Nurse
    template_name = 'nurses/nurse_list.html'
    context_object_name = 'nurses'
    paginate_by = 10
    required_roles = ['admin', 'hr_manager', 'doctor', 'nurse']

    def get_queryset(self):
        """Get nurses for unified ZAIN HMS system"""
        # ZAIN HMS unified system - all nurses in single database
        queryset = Nurse.objects.all()
        
        # Apply filters
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

class NurseCreateView(UnifiedSystemMixin, LoginRequiredMixin, CreateView):
    model = Nurse
    form_class = NurseForm
    template_name = 'nurses/nurse_form.html'
    success_url = reverse_lazy('nurses:nurse_list')
    required_roles = ['admin', 'hr_manager']

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # ZAIN HMS unified system - no database name needed
        return kwargs

    def form_valid(self, form):
        try:
            nurse = form.save(commit=False)
            
            # Check if user account should be created
            create_user = form.cleaned_data.get('create_user_account', True)  # Default to True
            
            if create_user and hasattr(form, 'cleaned_data'):
                try:
                    # Use UserManagementService to create user account
                    user = UserManagementService.create_user_account(
                        email=form.cleaned_data.get('email'),
                        first_name=form.cleaned_data.get('first_name'),
                        last_name=form.cleaned_data.get('last_name'),
                        role='NURSE',
                        username=form.cleaned_data.get('username'),  # Pass the generated username
                        password=form.cleaned_data.get('password'),  # Pass the actual password
                        created_by=self.request.user,
                        additional_data={
                            # Don't include nurse employee_id as it conflicts with user employee_id unique constraint
                            'phone': nurse.phone_number,
                        }
                    )
                    
                    # Link the nurse to the created user
                    nurse.user = user
                    
                    messages.success(
                        self.request,
                        f'Nurse {form.cleaned_data.get("first_name", "")} {form.cleaned_data.get("last_name", "")} created successfully! '
                        f'Login Details: '
                        f'Username: {form.cleaned_data.get("username", "")}, '
                        f'Password: As provided, '
                        f'Access: This hospital only. '
                        f'The nurse can now login to the system using their username and password.'
                    )
                except Exception as user_error:
                    # If user creation fails, still save the nurse but show warning
                    messages.warning(
                        self.request,
                        f'Nurse created but user account creation failed: {str(user_error)}. '
                        f'You can create the user account manually later.'
                    )
            else:
                # Create a minimal user account with username
                from apps.accounts.models import CustomUser
                import uuid
                
                try:
                    email = form.cleaned_data.get('email')
                    username = form.cleaned_data.get('username') or email
                    
                    if username and not CustomUser.objects.filter(username=username).exists():
                        user = CustomUser.objects.create_user(
                            username=username,  # Use username instead of email
                            email=email,
                            first_name=form.cleaned_data.get('first_name', ''),
                            last_name=form.cleaned_data.get('last_name', ''),
                            role='NURSE'
                        )
                        user.set_password(str(uuid.uuid4())[:8])  # Set temporary password
                        user.save()
                        nurse.user = user
                        
                        messages.success(
                            self.request,
                            f'Nurse and user account created successfully!<br>'
                            f'<strong>Login Details:</strong><br>'
                            f'• Username: <code>{username}</code><br>'
                            f'• Password: <em>Temporary password set</em><br>'
                            f'• Access: This hospital only<br>'
                            f'<small>Please provide login details to the nurse.</small>'
                        )
                    else:
                        messages.warning(
                            self.request,
                            f'Nurse created but user account already exists with this username.'
                        )
                except Exception as e:
                    messages.warning(
                        self.request,
                        f'Nurse created but could not create user account: {str(e)}'
                    )
                
            # ZAIN HMS unified system - save to default database
            print("Nurse saved to unified database")
            
            return super().form_valid(form)
            
        except Exception as e:
            messages.error(
                self.request,
                f'Error creating nurse: {str(e)}'
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
class ScheduleCreateView(UnifiedSystemMixin, LoginRequiredMixin, CreateView):
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

@login_required
def check_username_availability(request):
    """AJAX endpoint to check username availability across all hospitals"""
    from django.http import JsonResponse
    from apps.accounts.models import CustomUser
    from django.db import connections
    from django.conf import settings
    import os
    import re
    
    if request.method == 'GET':
        username = request.GET.get('username', '').strip().lower()
        first_name = request.GET.get('first_name', '').strip().lower()
        last_name = request.GET.get('last_name', '').strip().lower()
        
        if not username:
            return JsonResponse({'available': False, 'message': 'Username is required'})
        
        # Validate username format
        if not re.match(r'^[a-zA-Z0-9._-]+$', username):
            return JsonResponse({
                'available': False, 
                'message': 'Username can only contain letters, numbers, dots, underscores, and hyphens'
            })
        
        # Check across all databases
        taken_in = []
        
        # Check main database
        try:
            if CustomUser.objects.filter(username=username).exists():
                taken_in.append('main system')
        except Exception:
            pass
        
        # Unified system: only check the main database for username conflicts
        
        if taken_in:
            message = f"Username taken in: {', '.join(taken_in)}"
            suggestions = generate_username_suggestions(username, first_name, last_name)
            return JsonResponse({
                'available': False, 
                'message': message,
                'suggestions': suggestions
            })
        else:
            return JsonResponse({
                'available': True, 
                'message': 'Username is available!'
            })
    
    return JsonResponse({'available': False, 'message': 'Invalid request method'})

def generate_username_suggestions(username, first_name, last_name):
    """Generate username suggestions"""
    suggestions = []
    
    # Generate various suggestions based on name
    if first_name and last_name:
        suggestions.extend([
            f"{first_name}.{last_name}",
            f"{first_name[0]}.{last_name}",
            f"{first_name}.{last_name[0]}",
            f"{first_name}_{last_name}",
            f"{last_name}.{first_name}",
            f"{first_name}{last_name}",
        ])
    
    # Add numbered variations
    base = username
    for i in range(2, 8):
        suggestions.append(f"{base}{i}")
        if first_name and last_name:
            suggestions.append(f"{first_name}.{last_name}{i}")
    
    # Remove duplicates and the original username
    suggestions = list(dict.fromkeys(suggestions))  # Remove duplicates
    if username in suggestions:
        suggestions.remove(username)
        
    return suggestions[:6]  # Return top 6 suggestions