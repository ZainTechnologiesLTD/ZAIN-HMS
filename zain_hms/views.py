
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin


class ProfileView(LoginRequiredMixin,TemplateView):
    template_name = 'registration/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context
    
class CustomPasswordChangeView(SuccessMessageMixin, PasswordChangeView):
    template_name = 'change_password.html'  # Your existing template
    success_url = reverse_lazy('password_change_success')  # Redirect to a success page
    success_message = "Your password was changed successfully!"