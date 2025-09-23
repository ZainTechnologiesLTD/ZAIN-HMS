from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from . import views
# Removed single_hospital_auth import - using unified system
from .forms import CustomPasswordResetForm, CustomSetPasswordForm

app_name = 'accounts'

urlpatterns = [
    # Profile
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('password/change/', views.password_change_view, name='password_change'),
    
    # ZAIN HMS Unified System Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(
        template_name='accounts/logout.html',
        next_page='/accounts/login/'
    ), name='logout'),
    # Patient registration for unified hospital system
    path('register/', views.register_view, name='register'),
    path('signup/', views.register_view, name='signup'),
    path('check-username/', views.check_username_availability, name='check_username'),
    
    # User Management URLs
    path('users/', views.user_list_view, name='user_list'),
    path('user-management/', views.user_list_view, name='user_management'),
    path('users/add/', views.UserCreateView.as_view(), name='user_create'),
    path('users/create/', views.user_create_view, name='user_create_alt'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('users/<int:pk>/edit/', views.UserUpdateView.as_view(), name='user_edit'),
    path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),
    # Removed check_username_availability - using unified system
    
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
