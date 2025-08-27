from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views
from .single_hospital_auth import SingleHospitalLoginView, check_username_availability, signup_hospital_user
from .forms import CustomPasswordResetForm, CustomSetPasswordForm

app_name = 'accounts'

urlpatterns = [
    # Profile
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    
    # Single Hospital Authentication (New Approach)
    path('login/', SingleHospitalLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', signup_hospital_user, name='register'),
    path('signup/', signup_hospital_user, name='signup'),
    path('check-username/', check_username_availability, name='check_username'),
    
    # Tenant Selection URLs
    path('tenant-selection/', views.tenant_selection_view, name='tenant_selection'),
    path('hospital-selection/', views.tenant_selection_view, name='hospital_selection'),  # Alias for backward compatibility
    path('select-hospital/<slug:hospital_id>/', views.select_hospital, name='select_hospital'),
    path('multi-tenant-selection/', views.multi_tenant_selection_view, name='multi_tenant_selection'),
    path('clear-hospital-selection/', views.clear_hospital_selection_view, name='clear_hospital_selection'),
    
    # User Management URLs
    path('users/', views.user_list_view, name='user_list'),
    path('user-management/', views.user_list_view, name='user_management'),
    
    # Password Change URLs
    path('change-password/', 
         auth_views.PasswordChangeView.as_view(
             template_name='accounts/change_password.html',
             success_url=reverse_lazy('accounts:change_password_done')
         ), 
         name='change_password'),
    
    path('change-password/done/', 
         auth_views.PasswordChangeDoneView.as_view(
             template_name='accounts/change_password_done.html'
         ), 
         name='change_password_done'),
    
    # Password Reset URLs
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             email_template_name='accounts/password_reset_email.html',
             form_class=CustomPasswordResetForm,
             success_url=reverse_lazy('accounts:password_reset_done')
         ), 
         name='password_reset'),
    
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ), 
         name='password_reset_done'),
    
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html',
             form_class=CustomSetPasswordForm,
             success_url=reverse_lazy('accounts:password_reset_complete')
         ), 
         name='password_reset_confirm'),
    
    path('password-reset/complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
]
