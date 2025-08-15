# apps/accounts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, UpdateView, CreateView
from django.urls import reverse_lazy
from django.db.models import Q
from django.utils import timezone
from django.core.paginator import Paginator
from .models import User, Hospital, UserSession
from .forms import (
    CustomAuthenticationForm, UserRegistrationForm,
    UserProfileForm, StaffRegistrationForm
)

def login_view(request):
    """Enhanced login view"""
    if request.user.is_authenticated:
        return redirect('dashboard:home')
        
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Update last activity
            user.last_activity = timezone.now()
            user.save(update_fields=['last_activity'])
            
            # Create session record
            UserSession.objects.create(
                user=user,
                session_key=request.session.session_key,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Remember me functionality
            if not form.cleaned_data.get('remember_me'):
                request.session.set_expiry(0)
                
            messages.success(request, f'Welcome back, {user.get_display_name()}!')
            
            next_url = request.GET.get('next', 'dashboard:home')
            return redirect(next_url)
    else:
        form = CustomAuthenticationForm(request)
        
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """Logout view"""
    if request.user.is_authenticated:
        # Invalidate user session
        UserSession.objects.filter(
            user=request.user,
            session_key=request.session.session_key
        ).update(is_active=False)
        
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('accounts:login')


def register_view(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('dashboard:home')
        
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            
            # Auto-approve patients, others need admin approval
            if user.role == 'PATIENT':
                user.is_approved = True
                user.approved_at = timezone.now()
            
            user.save()
            
            if user.role == 'PATIENT':
                login(request, user)
                messages.success(request, 'Registration successful! Welcome to ZAIN HMS.')
                return redirect('dashboard:home')
            else:
                messages.info(request, 'Registration successful! Your account is pending approval.')
                return redirect('accounts:login')
    else:
        form = UserRegistrationForm()
        
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile_view(request):
    """User profile view"""
    user = request.user
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=user)
        
    context = {
        'form': form,
        'user': user,
    }
    
    return render(request, 'accounts/profile.html', context)


@login_required
def change_password_view(request):
    """Change password view"""
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not request.user.check_password(old_password):
            messages.error(request, 'Current password is incorrect.')
        elif new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
        elif len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
        else:
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Password changed successfully!')
            return redirect('accounts:profile')
            
    return render(request, 'accounts/change_password.html')


class UserManagementView(LoginRequiredMixin, ListView):
    """User management view for admins"""
    model = User
    template_name = 'accounts/user_management.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in ['ADMIN', 'SUPERADMIN']:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = User.objects.filter(hospital=self.request.user.hospital)
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search) |
                Q(employee_id__icontains=search)
            )
            
        # Filter by role
        role = self.request.GET.get('role')
        if role:
            queryset = queryset.filter(role=role)
            
        # Filter by status
        status = self.request.GET.get('status')
        if status == 'pending':
            queryset = queryset.filter(is_approved=False)
        elif status == 'approved':
            queryset = queryset.filter(is_approved=True)
        elif status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
            
        return queryset.order_by('-date_joined')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['roles'] = User.ROLE_CHOICES
        context['pending_count'] = User.objects.filter(
            hospital=self.request.user.hospital,
            is_approved=False
        ).count()
        return context


@login_required
def approve_user(request, user_id):
    """Approve user registration"""
    if request.user.role not in ['ADMIN', 'SUPERADMIN']:
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('dashboard:home')
        
    user = get_object_or_404(User, id=user_id, hospital=request.user.hospital)
    user.is_approved = True
    user.approved_by = request.user
    user.approved_at = timezone.now()
    user.save()
    
    messages.success(request, f'User {user.get_full_name()} has been approved.')
    
    # TODO: Send email notification to user
    
    return redirect('accounts:user_management')


@login_required
def toggle_user_status(request, user_id):
    """Toggle user active status"""
    if request.user.role not in ['ADMIN', 'SUPERADMIN']:
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('dashboard:home')
        
    user = get_object_or_404(User, id=user_id, hospital=request.user.hospital)
    user.is_active = not user.is_active
    user.save()
    
    status = 'activated' if user.is_active else 'deactivated'
    messages.success(request, f'User {user.get_full_name()} has been {status}.')
    
    return redirect('accounts:user_management')


class CreateStaffView(LoginRequiredMixin, CreateView):
    """Create new staff member"""
    model = User
    form_class = StaffRegistrationForm
    template_name = 'accounts/create_staff.html'
    success_url = reverse_lazy('accounts:user_management')
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in ['ADMIN', 'SUPERADMIN', 'HR_MANAGER']:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['hospital'] = self.request.user.hospital
        return kwargs
    
    def form_valid(self, form):
        user = form.save(commit=False)
        user.hospital = self.request.user.hospital
        user.is_approved = True
        user.approved_by = self.request.user
        user.approved_at = timezone.now()
        
        # Generate employee ID
        last_employee = User.objects.filter(
            hospital=user.hospital,
            employee_id__isnull=False
        ).order_by('-employee_id').first()
        
        if last_employee and last_employee.employee_id:
            try:
                last_number = int(last_employee.employee_id.split('-')[-1])
                new_number = last_number + 1
            except:
                new_number = 1
        else:
            new_number = 1
            
        user.employee_id = f"{user.hospital.code}-{user.role[:3]}-{new_number:05d}"
        user.save()
        
        messages.success(self.request, f'Staff member {user.get_full_name()} created successfully.')
        return super().form_valid(form)