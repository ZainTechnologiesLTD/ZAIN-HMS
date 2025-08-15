# dashboard/views.py
from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin



class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/index.html'
    login_url = '/login/'  # Specify where to redirect if not logged in

