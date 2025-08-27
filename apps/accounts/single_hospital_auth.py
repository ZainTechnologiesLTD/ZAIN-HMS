# apps/accounts/single_hospital_auth.py
from django.contrib.auth.views import LoginView
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages
import logging
logger = logging.getLogger(__name__)
from django.urls import reverse_lazy
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse
from apps.accounts.models import CustomUser
from apps.tenants.models import Tenant

class SingleHospitalLoginView(LoginView):
    """
    Custom login view that enforces single hospital per user approach.
    After login, users are directly redirected to their hospital dashboard.
    """
    template_name = 'registration/login.html'
    success_url = reverse_lazy('dashboard:dashboard')
    
    def form_valid(self, form):
        """Handle successful login"""
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        
        # Authenticate user
        user = authenticate(self.request, username=username, password=password)
        
        if user is not None:
            # If user has no hospital assigned, try to persist a session-selected
            # hospital (selection UI may have stored it in session) before
            # rejecting the login for non-superadmins.
            if not user.hospital:
                hid = None
                for key in ('current_hospital_id', 'selected_hospital_id', 'selected_hospital_code'):
                    if self.request.session.get(key):
                        hid = self.request.session.get(key)
                        break

                if hid:
                    tenant = None
                    try:
                        if str(hid).isdigit():
                            tenant = Tenant.objects.using('default').get(id=int(hid))
                        else:
                            try:
                                tenant = Tenant.objects.using('default').get(subdomain=hid)
                            except Tenant.DoesNotExist:
                                tenant = Tenant.objects.using('default').get(db_name=hid)
                    except Exception:
                        tenant = None

                    if tenant:
                        try:
                            logger.info('Attempting to persist session-selected tenant %s to user %s', getattr(tenant,'id',None), getattr(user,'username',None))
                            before = getattr(user, 'hospital_id', None)
                            logger.info('user.hospital before: %s', before)
                            user.hospital = tenant
                            user.save(using='default')
                            after = getattr(user, 'hospital_id', None)
                            logger.info('user.hospital after: %s', after)
                        except Exception as e:
                            logger.exception('Failed to persist tenant to user: %s', e)

            # Check if user has hospital assigned after attempting session persistence
            if user.role != 'SUPERADMIN' and not user.hospital:
                messages.error(self.request, 'Your account is not assigned to any hospital. Please contact administrator.')
                return redirect('accounts:login')

            # Login user
            login(self.request, user)
            
            # Success message with hospital info
            if user.hospital:
                messages.success(self.request, f'Welcome to {user.hospital.name}!')
            else:
                messages.success(self.request, 'Welcome, Super Administrator!')
            
            # Redirect based on user role
            if user.role == 'HOSPITAL_ADMIN':
                return redirect('tenants:hospital_profile')
            elif user.role == 'DOCTOR':
                return redirect('dashboard:dashboard')
            elif user.role in ['NURSE', 'RECEPTIONIST']:
                return redirect('patients:patient_list')
            else:
                return redirect('dashboard:dashboard')
        
        # Authentication failed
        messages.error(self.request, 'Invalid username or password.')
        return redirect('accounts:login')


def check_username_availability(request):
    """API endpoint to check if username is available"""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        
        if not username:
            return JsonResponse({'available': False, 'message': 'Username is required'})
        
        # Check if username already exists
        if CustomUser.objects.filter(username=username).exists():
            return JsonResponse({
                'available': False, 
                'message': f'Username "{username}" is already taken. Please choose a different username.'
            })
        
        return JsonResponse({
            'available': True, 
            'message': f'Username "{username}" is available.'
        })
    
    return JsonResponse({'available': False, 'message': 'Invalid request'})


def signup_hospital_user(request):
    """Create new user for a specific hospital"""
    if request.method == 'POST':
        # Get form data
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        role = request.POST.get('role', 'STAFF')
        hospital_id = request.POST.get('hospital_id')
        
        # Validation
        errors = []
        
        if not username:
            errors.append('Username is required.')
        elif CustomUser.objects.filter(username=username).exists():
            errors.append(f'Username "{username}" is already taken.')
        
        if not email:
            errors.append('Email is required.')
        elif CustomUser.objects.filter(email=email).exists():
            errors.append('Email is already registered.')
        
        if not password:
            errors.append('Password is required.')
        elif len(password) < 8:
            errors.append('Password must be at least 8 characters long.')
        
        if password != confirm_password:
            errors.append('Passwords do not match.')
        
        if not hospital_id:
            errors.append('Hospital selection is required.')
        
        # Check hospital exists
        try:
            hospital = Tenant.objects.get(id=hospital_id, is_active=True)
        except Tenant.DoesNotExist:
            errors.append('Selected hospital is not valid.')
            hospital = None
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'registration/signup.html', {
                'hospitals': Tenant.objects.filter(is_active=True),
                'form_data': request.POST
            })
        
        # Create user
        try:
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role=role,
                hospital=hospital
            )
            
            messages.success(request, f'Account created successfully for {hospital.name}! You can now login.')
            return redirect('accounts:login')
            
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return render(request, 'registration/signup.html', {
                'hospitals': Tenant.objects.filter(is_active=True),
                'form_data': request.POST
            })
    
    # GET request - show signup form
    hospitals = Tenant.objects.filter(is_active=True)
    return render(request, 'registration/signup.html', {'hospitals': hospitals})
