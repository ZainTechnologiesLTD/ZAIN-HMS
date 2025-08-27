from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from django.core.paginator import Paginator
from django.http import JsonResponse
from .forms import LoginForm, RegistrationForm
from .models import CustomUser
from apps.tenants.models import Tenant
from django import forms

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)

                # If a hospital was selected in session (selection UI), persist
                # it to the user record (saved in the shared 'default' DB) so
                # subsequent views relying on user.get_current_hospital() work.
                for key in ('current_hospital_id', 'selected_hospital_id', 'selected_hospital_code'):
                    hid = request.session.get(key)
                    if not hid:
                        continue

                    tenant = None
                    try:
                        # Try by numeric id first
                        if str(hid).isdigit():
                            tenant = Tenant.objects.using('default').get(id=int(hid))
                        else:
                            # Try by subdomain or db_name
                            try:
                                tenant = Tenant.objects.using('default').get(subdomain=hid)
                            except Tenant.DoesNotExist:
                                tenant = Tenant.objects.using('default').get(db_name=hid)
                    except Exception:
                        tenant = None

                    if tenant:
                        try:
                            user.hospital = tenant
                            user.save(using='default')
                        except Exception:
                            # don't fail the login if persistence fails
                            pass
                        break

                # Redirect to dashboard after successful login
                next_url = request.GET.get('next', 'dashboard:home')
                return redirect(next_url)
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('accounts:login')

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profile_view(request):
    """Render the user profile page."""
    return render(request, 'accounts/profile.html', {})

class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone', 'address']

@login_required
def profile_edit_view(request):
    """Minimal profile edit implementation wiring to existing template."""
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')
    else:
        form = ProfileEditForm(instance=request.user)
    return render(request, 'accounts/profile_edit.html', { 'form': form })

@login_required
def tenant_selection_view(request):
    """Tenant selection for SUPERADMIN users"""
    if request.user.role != 'SUPERADMIN':
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        tenant_id = request.POST.get('tenant_id')
        if tenant_id:
            try:
                tenant = None  # Tenant.objects.get(id=tenant_id)  # Temporarily commented
                request.session['selected_tenant_id'] = tenant.id
                request.session['selected_tenant_name'] = tenant.name
                messages.success(request, f'Selected hospital: {tenant.name}')
                return redirect('dashboard:home')
            except:  # Tenant.DoesNotExist:  # Temporarily commented
                messages.error(request, 'Invalid hospital selected.')
    
    tenants = []  # Tenant.objects.all()  # Temporarily commented
    return render(request, 'accounts/tenant_selection.html', {'tenants': tenants})

@login_required
def multi_tenant_selection_view(request):
    """Multi-tenant selection for users with multiple tenant affiliations"""
    # Get user's tenant affiliations (if the model exists)
    # For now, we'll use a simple approach
    
    if request.method == 'POST':
        tenant_id = request.POST.get('tenant_id')
        if tenant_id:
            try:
                tenant = None  # Tenant.objects.get(id=tenant_id)  # Temporarily commented
                # Verify user has access to this tenant
                if (request.user.tenant == tenant or 
                    request.user.role in ['SUPERADMIN', 'ADMIN']):
                    request.session['selected_tenant_id'] = tenant.id
                    request.session['selected_tenant_name'] = tenant.name
                    messages.success(request, f'Selected hospital: {tenant.name}')
                    return redirect('dashboard:home')
                else:
                    messages.error(request, 'You do not have access to this hospital.')
            except:  # Tenant.DoesNotExist:  # Temporarily commented
                messages.error(request, 'Invalid hospital selected.')
    
    # Get available tenants for this user
    if request.user.is_superuser:
        # Super admins can see all tenants
        tenants = []  # Tenant.objects.all()  # Temporarily commented
    else:
        # For regular users, show their assigned tenant and any additional affiliations
        tenants = []  # Tenant.objects.filter(Q(id=request.user.tenant_id))  # Temporarily commented
    
    return render(request, 'accounts/multi_tenant_selection.html', {'tenants': tenants})

@login_required
def user_list_view(request):
    """User management list view for ADMIN and SUPERADMIN"""
    if request.user.role not in ['ADMIN', 'SUPERADMIN'] and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access user management.')
        return redirect('dashboard:home')
    
    # Get users based on role
    if request.user.role == 'SUPERADMIN':
        users = CustomUser.objects.all()
    else:
        # ADMIN can only see users from their selected hospital
        selected_hospital_id = request.session.get('selected_hospital_id')
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

@login_required
def clear_hospital_selection_view(request):
    """Clear the hospital selection and go back to selection page"""
    if 'selected_tenant_id' in request.session:
        del request.session['selected_tenant_id']
    if 'selected_tenant_name' in request.session:
        del request.session['selected_tenant_name']
    
    messages.info(request, 'Hospital selection cleared.')
    return redirect('accounts:tenant_selection')


@login_required
def select_hospital(request, hospital_id: str):
    """AJAX endpoint to select a hospital from the Accounts selection UI.
    Accepts a slug/UUID/string ID, stores it in session, and returns JSON.
    """
    # In this simplified setup we don't resolve to a DB object here.
    # We just persist the provided identifier and redirect home.
    request.session['selected_hospital_id'] = str(hospital_id)
    request.session['selected_hospital_code'] = str(hospital_id)
    request.session['selected_hospital_name'] = str(hospital_id)

    # Prefer JSON for the template's fetch() handler
    return JsonResponse({
        'success': True,
        'message': f'Selected hospital: {hospital_id}',
        'redirect_url': '/dashboard/',
    })
