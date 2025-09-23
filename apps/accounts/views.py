from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LogoutView
from django.contrib import messages
from django.db import models
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.generic import CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.utils.translation import get_language
from .forms import LoginForm, RegistrationForm, UserCreateForm, UserUpdateForm
from .models import CustomUser
# from apps.core.db_router import TenantDatabaseManager  # Removed for unified ZAIN HMS
from django import forms
import logging

# Setup logging for user authentication
logger = logging.getLogger(__name__)

def get_tenant_from_request(request):
    """Get tenant from request subdomain - ZAIN HMS unified system"""
    # ZAIN HMS unified system - no tenant needed
    return None

def login_view(request):
    if request.method == 'POST':
        # Lightweight endpoint to set captcha expected value (JSON/XHR)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            try:
                import json
                payload = json.loads(request.body.decode() or '{}')
                if payload.get('set_captcha') and 'expected' in payload:
                    request.session['captcha_expected'] = str(payload['expected'])
                    return JsonResponse({'status': 'ok'})
            except Exception:
                return JsonResponse({'status': 'error'}, status=400)
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                
                # Log successful login for security monitoring
                logger.info(f"User {user.username} logged in to ZAIN HMS")

                # ZAIN HMS unified system - no tenant context needed
                
                # Redirect to dashboard after successful login
                current_language = get_language()
                next_url = request.GET.get('next', f'/{current_language}/dashboard/')
                return redirect(next_url)
            else:
                # Invalid credentials
                messages.error(request, 'Invalid username or password. Please try again.')
                logger.warning(f"Failed login attempt for username: {username}")
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def logout_view(request):
    """
    Handle user logout with proper CSRF protection
    """
    if request.method == 'POST':
        # POST logout with CSRF protection
        current_language = get_language()
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
        return redirect(f'/{current_language}/accounts/login/')
    else:
        # GET request - show logout confirmation page or redirect to login
        current_language = get_language()
        return redirect(f'/{current_language}/accounts/login/')


class CustomLogoutView(LogoutView):
    """
    Custom logout view with proper language-aware redirects and CSRF protection
    """
    template_name = 'accounts/logout.html'
    http_method_names = ['get', 'post']  # Allow both GET and POST
    
    def get_next_page(self):
        """Override to provide language-aware redirect"""
        current_language = get_language()
        return f'/{current_language}/accounts/login/'
    
    def get(self, request, *args, **kwargs):
        """Handle GET requests - show logout confirmation form"""
        return render(request, self.template_name)
    
    def post(self, request, *args, **kwargs):
        """Handle POST requests - perform logout"""
        # Log logout for security monitoring
        if request.user.is_authenticated:
            logger.info(f"User {request.user.username} logged out from ZAIN HMS")
        
        messages.success(request, 'You have been successfully logged out.')
        return super().post(request, *args, **kwargs)

def register_view(request):
    # ZAIN HMS unified system - no tenant context needed
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registration successful! Please login.')
            return redirect('accounts:login')
    else:
        form = RegistrationForm()

    context = {
        'form': form,
    }
    return render(request, 'registration/signup.html', context)

@login_required
def profile_view(request):
    """Enhanced user profile page with stats and user data."""
    context = {}
    
    # Get user stats based on role
    if request.user.role == 'DOCTOR':
        try:
            # Get doctor-specific stats
            from apps.doctors.models import Doctor
            from apps.appointments.models import Appointment
            
            doctor = Doctor.objects.get(user=request.user)
            context.update({
                'appointments_count': Appointment.objects.filter(doctor=doctor).count(),
                'patients_count': Appointment.objects.filter(doctor=doctor).values('patient').distinct().count(),
                'completed_appointments': Appointment.objects.filter(doctor=doctor, status='COMPLETED').count(),
            })
        except:
            context.update({
                'appointments_count': 0,
                'patients_count': 0, 
                'completed_appointments': 0,
            })
    
    # Get notification count
    try:
        from apps.notifications.models import Notification
        context['notifications_count'] = Notification.objects.filter(
            user=request.user, is_read=False
        ).count()
    except:
        context['notifications_count'] = 0
    
    # Add reports count for admin roles
    if request.user.role in ['ADMIN', 'SUPERADMIN', 'ADMIN']:
        context['reports_count'] = 15  # Placeholder - implement actual reports count
    else:
        context['reports_count'] = 0
    
    return render(request, 'accounts/profile.html', context)

class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'date_of_birth', 'gender', 'profile_picture']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

@login_required
def profile_edit_view(request):
    """Enhanced profile edit with image upload support."""
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')
    else:
        form = ProfileEditForm(instance=request.user)
    return render(request, 'accounts/profile_edit.html', { 'form': form })

class CustomPasswordChangeForm(forms.Form):
    """Enhanced password change form with validation"""
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your current password'
        }),
        label='Current Password'
    )
    new_password = forms.CharField(
        min_length=8,  # Changed from 12 to 8
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password (minimum 8 characters)'
        }),
        label='New Password',
        help_text='Password must be at least 8 characters long.'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        }),
        label='Confirm New Password'
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise forms.ValidationError('Current password is incorrect.')
        return current_password
    
    def clean_confirm_password(self):
        new_password = self.cleaned_data.get('new_password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if new_password and confirm_password:
            if new_password != confirm_password:
                raise forms.ValidationError('New passwords do not match.')
        return confirm_password
    
    def save(self):
        new_password = self.cleaned_data['new_password']
        self.user.set_password(new_password)
        self.user.save()
        return self.user

@login_required
def password_change_view(request):
    """Enhanced password change view"""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            # Update session to prevent logout after password change
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Your password has been changed successfully!')
            return redirect('accounts:profile')
    else:
        form = CustomPasswordChangeForm(request.user)
    
    return render(request, 'accounts/password_change.html', {'form': form})

@login_required
def user_list_view(request):
    """User management list view for SUPERADMIN, ADMIN and HOSPITAL_ADMIN"""
    # Allow SUPERADMIN, ADMIN and HOSPITAL_ADMIN roles (and Django superusers)
    if request.user.role not in ['ADMIN', 'SUPERADMIN', 'ADMIN'] and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access user management.')
        return redirect('dashboard:home')

    # Get users based on role
    # - True super administrators (role == 'SUPERADMIN') can see all users.
    # - Hospital administrators should only see users belonging to their own hospital
    #   even if their is_superuser flag was (incorrectly) set in the DB.
    # - Other allowed roles use the session-selected hospital or the user's assigned hospital.
    if request.user.role == 'SUPERADMIN' or (request.user.is_superuser and request.user.role == 'SUPERADMIN'):
        users = CustomUser.objects.all()
    elif request.user.role == 'ADMIN':
        # Always scope hospital admins to their configured hospital
        if getattr(request.user, 'hospital', None):
            users = CustomUser.objects.filter(hospital_id=request.user.hospital.id)
        else:
            users = CustomUser.objects.none()
    else:
        # Prefer session-selected hospital, fall back to user's assigned hospital
        selected_hospital_id = request.session.get('selected_hospital_id')
        if not selected_hospital_id:
            if getattr(request.user, 'hospital', None):
                selected_hospital_id = getattr(request.user.hospital, 'id', None)

        if selected_hospital_id:
            users = CustomUser.objects.filter(hospital_id=selected_hospital_id)
        else:
            users = CustomUser.objects.none()
    
    # Add search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            models.Q(username__icontains=search_query) |
            models.Q(first_name__icontains=search_query) |
            models.Q(last_name__icontains=search_query) |
            models.Q(email__icontains=search_query)
        )
    
    # Add role filter
    role_filter = request.GET.get('role', '')
    if role_filter:
        users = users.filter(role=role_filter)
    
    # Pagination
    paginator = Paginator(users.order_by('username'), 20)
    page_number = request.GET.get('page')
    users_page = paginator.get_page(page_number)
    
    # Get all role choices for filter dropdown
    role_choices = CustomUser.ROLE_CHOICES
    
    context = {
        'users': users_page,
        'search_query': search_query,
        'role_filter': role_filter,
        'role_choices': role_choices,
    }
    
    return render(request, 'accounts/user_list.html', context)


@method_decorator(login_required, name='dispatch')
class UserCreateView(CreateView):
    """View for creating new users - SECURITY: Only ADMIN and SUPERADMIN can create users"""
    model = CustomUser
    form_class = UserCreateForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user_list')
    
    def dispatch(self, request, *args, **kwargs):
        """SECURITY: Check if user has permission to create users"""
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        # Only ADMIN and SUPERADMIN can create users
        if request.user.role not in ['ADMIN', 'SUPERADMIN']:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to create users.")
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass current user to form for role filtering
        kwargs['current_user'] = self.request.user
        
        # Pass current hospital to form if available
        if hasattr(self.request.user, 'hospital') and self.request.user.hospital:
            kwargs['initial'] = kwargs.get('initial', {})
        return kwargs
    
    def form_valid(self, form):
        # Set the hospital for the new user if current user has one
        if hasattr(self.request.user, 'hospital') and self.request.user.hospital:
            form.instance.hospital = self.request.user.hospital
            # Also store hospital in form for save method
            form._hospital = self.request.user.hospital
        
        messages.success(self.request, f'User "{form.instance.username}" created successfully!')
        return super().form_valid(form)
    
    def dispatch(self, request, *args, **kwargs):
        # Only allow admin users to create users
        if request.user.role not in ['ADMIN', 'SUPERADMIN', 'ADMIN']:
            messages.error(request, 'You do not have permission to create users.')
            return redirect('accounts:user_list')
        return super().dispatch(request, *args, **kwargs)


@login_required
def user_create_view(request):
    """Function-based view for creating users"""
    if request.user.role not in ['ADMIN', 'SUPERADMIN']:
        messages.error(request, 'You do not have permission to create users.')
        return redirect('accounts:user_list')
    
    if request.method == 'POST':
        form = UserCreateForm(request.POST, current_user=request.user)
        if hasattr(request.user, 'hospital') and request.user.hospital:
            form._hospital = request.user.hospital
            
        if form.is_valid():
            user = form.save(commit=False)
            if hasattr(request.user, 'hospital') and request.user.hospital:
                user.hospital = request.user.hospital
            user.save()
            messages.success(request, f'User "{user.username}" created successfully!')
            return redirect('accounts:user_list')
    else:
        form = UserCreateForm(current_user=request.user)
    
    return render(request, 'accounts/user_form.html', {'form': form})

@method_decorator(login_required, name='dispatch')
class UserDetailView(DetailView):
    """View for displaying user details"""
    model = CustomUser
    template_name = 'accounts/user_detail.html'
    context_object_name = 'user_detail'
    
    def dispatch(self, request, *args, **kwargs):
        # Only allow admin users to view user details
        if request.user.role not in ['ADMIN', 'SUPERADMIN', 'ADMIN']:
            messages.error(request, 'You do not have permission to view user details.')
            return redirect('accounts:user_list')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        # ZAIN HMS unified system - all users visible to authorized staff
        return CustomUser.objects.all()


@method_decorator(login_required, name='dispatch')
class UserUpdateView(UpdateView):
    """View for updating user details"""
    model = CustomUser
    form_class = UserUpdateForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user_list')
    
    def dispatch(self, request, *args, **kwargs):
        # Only allow admin users to edit users
        if request.user.role not in ['ADMIN', 'SUPERADMIN', 'ADMIN']:
            messages.error(request, 'You do not have permission to edit users.')
            return redirect('accounts:user_list')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        # ZAIN HMS unified system - all users editable by authorized staff
        return CustomUser.objects.all()
    
    def form_valid(self, form):
        messages.success(self.request, f'User "{form.instance.username}" updated successfully!')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class UserDeleteView(DeleteView):
    """View for deleting users"""
    model = CustomUser
    template_name = 'accounts/user_confirm_delete.html'
    success_url = reverse_lazy('accounts:user_list')
    
    def dispatch(self, request, *args, **kwargs):
        # Only allow admin users to delete users
        if request.user.role not in ['ADMIN', 'SUPERADMIN', 'ADMIN']:
            messages.error(request, 'You do not have permission to delete users.')
            return redirect('accounts:user_list')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        # ZAIN HMS unified system - all users deletable by authorized staff
        return CustomUser.objects.all()
    
    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        username = user.username
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'User "{username}" deleted successfully!')
        return response


@login_required
def check_username_availability(request):
    """
    AJAX endpoint to check username availability for unified ZAIN HMS system
    """
    username = request.POST.get('username', '').strip()
    if not username:
        return JsonResponse({'available': False, 'message': 'Username is required'})
    
    try:
        # Unified system: check the main database for username conflicts
        if CustomUser.objects.filter(username=username).exists():
            return JsonResponse({
                'available': False,
                'message': f'Username "{username}" already exists in the system'
            })

        return JsonResponse({'available': True, 'message': f'Username "{username}" is available'})

    except Exception as e:
        return JsonResponse({
            'available': False,
            'message': 'Error checking username availability'
        }, status=500)
