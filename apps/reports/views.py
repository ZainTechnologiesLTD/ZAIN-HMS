# apps/reports/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from apps.accounts.models import Hospital, User
from apps.patients.models import Patient
from apps.appointments.models import Appointment
from apps.billing.models import Bill
from apps.emergency.models import EmergencyCase
from .models import Report, ReportTemplate
from .forms import ReportGenerationForm, ReportTemplateForm
import json

class ReportListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all reports"""
    model = Report
    template_name = 'reports/report_list.html'
    context_object_name = 'reports'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.has_module_permission('reports')
    
    def get_queryset(self):
        hospital = getattr(self.request, 'hospital', None)
        if hospital:
            return Report.objects.filter(hospital=hospital).order_by('-created_at')
        return Report.objects.none()


class GenerateReportView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Generate new report"""
    model = Report
    form_class = ReportGenerationForm
    template_name = 'reports/generate_report.html'
    success_url = reverse_lazy('reports:report_list')
    
    def test_func(self):
        return self.request.user.has_module_permission('reports')
    
    def form_valid(self, form):
        hospital = getattr(self.request, 'hospital', None)
        form.instance.hospital = hospital
        form.instance.generated_by = self.request.user
        messages.success(self.request, 'Report generation started. You will be notified when ready.')
        return super().form_valid(form)


class ReportDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """View report details"""
    model = Report
    template_name = 'reports/report_detail.html'
    context_object_name = 'report'
    
    def test_func(self):
        return self.request.user.has_module_permission('reports')
    
    def get_queryset(self):
        hospital = getattr(self.request, 'hospital', None)
        if hospital:
            return Report.objects.filter(hospital=hospital)
        return Report.objects.none()


class ReportTemplateListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List report templates"""
    model = ReportTemplate
    template_name = 'reports/template_list.html'
    context_object_name = 'templates'
    
    def test_func(self):
        return self.request.user.has_module_permission('reports')
    
    def get_queryset(self):
        hospital = getattr(self.request, 'hospital', None)
        if hospital:
            return ReportTemplate.objects.filter(hospital=hospital, is_active=True)
        return ReportTemplate.objects.none()


class ReportTemplateCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create report template"""
    model = ReportTemplate
    form_class = ReportTemplateForm
    template_name = 'reports/template_form.html'
    success_url = reverse_lazy('reports:template_list')
    
    def test_func(self):
        return self.request.user.role in ['ADMIN', 'SUPERADMIN'] or self.request.user.is_superuser
    
    def form_valid(self, form):
        hospital = getattr(self.request, 'hospital', None)
        form.instance.hospital = hospital
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class ReportTemplateUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update report template"""
    model = ReportTemplate
    form_class = ReportTemplateForm
    template_name = 'reports/template_form.html'
    success_url = reverse_lazy('reports:template_list')
    
    def test_func(self):
        return self.request.user.role in ['ADMIN', 'SUPERADMIN'] or self.request.user.is_superuser


@login_required
def download_report(request, pk):
    """Download generated report"""
    hospital = getattr(request, 'hospital', None)
    report = get_object_or_404(Report, pk=pk, hospital=hospital)
    
    if report.file:
        response = HttpResponse(report.file.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{report.name}.{report.format.lower()}"'
        return response
    else:
        messages.error(request, 'Report file not found.')
        return redirect('reports:report_list')


@login_required
def delete_report(request, pk):
    """Delete report"""
    if request.method == 'POST':
        hospital = getattr(request, 'hospital', None)
        report = get_object_or_404(Report, pk=pk, hospital=hospital)
        report.delete()
        messages.success(request, 'Report deleted successfully.')
    
    return redirect('reports:report_list')


@login_required
def use_template(request, pk):
    """Use template to generate report"""
    hospital = getattr(request, 'hospital', None)
    template = get_object_or_404(ReportTemplate, pk=pk, hospital=hospital)
    
    # Pre-fill form with template data
    initial_data = {
        'name': f"{template.name} - {timezone.now().date()}",
        'report_type': template.report_type,
        'filters': template.default_filters
    }
    
    return render(request, 'reports/generate_report.html', {
        'template': template,
        'initial_data': initial_data
    })


@login_required
def patients_report(request):
    """Quick patients report"""
    hospital = getattr(request, 'hospital', None)
    
    # Get date range
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    data = {
        'total_patients': Patient.objects.filter(hospital=hospital).count(),
        'new_this_week': Patient.objects.filter(
            hospital=hospital, created_at__date__gte=week_ago
        ).count(),
        'new_this_month': Patient.objects.filter(
            hospital=hospital, created_at__date__gte=month_ago
        ).count(),
        'by_gender': Patient.objects.filter(hospital=hospital).values('gender').annotate(
            count=Count('id')
        ),
        'by_blood_group': Patient.objects.filter(hospital=hospital).values('blood_group').annotate(
            count=Count('id')
        )
    }
    
    return JsonResponse(data)


@login_required
def appointments_report(request):
    """Quick appointments report"""
    hospital = getattr(request, 'hospital', None)
    
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    data = {
        'total_appointments': Appointment.objects.filter(hospital=hospital).count(),
        'this_week': Appointment.objects.filter(
            hospital=hospital, appointment_date__gte=week_ago
        ).count(),
        'today': Appointment.objects.filter(
            hospital=hospital, appointment_date=today
        ).count(),
        'by_status': Appointment.objects.filter(hospital=hospital).values('status').annotate(
            count=Count('id')
        ),
        'by_type': Appointment.objects.filter(hospital=hospital).values('appointment_type').annotate(
            count=Count('id')
        )
    }
    
    return JsonResponse(data)


@login_required
def billing_report(request):
    """Quick billing report"""
    hospital = getattr(request, 'hospital', None)
    
    today = timezone.now().date()
    month_ago = today - timedelta(days=30)
    
    data = {
        'total_bills': Bill.objects.filter(hospital=hospital).count(),
        'total_revenue': Bill.objects.filter(
            hospital=hospital, status='PAID'
        ).aggregate(total=Sum('total_amount'))['total'] or 0,
        'this_month_revenue': Bill.objects.filter(
            hospital=hospital, status='PAID', created_at__date__gte=month_ago
        ).aggregate(total=Sum('total_amount'))['total'] or 0,
        'pending_amount': Bill.objects.filter(
            hospital=hospital, status='PENDING'
        ).aggregate(total=Sum('total_amount'))['total'] or 0,
        'by_status': Bill.objects.filter(hospital=hospital).values('status').annotate(
            count=Count('id')
        )
    }
    
    return JsonResponse(data)


@login_required
def financial_report(request):
    """Quick financial report"""
    hospital = getattr(request, 'hospital', None)
    
    today = timezone.now().date()
    dates = [(today - timedelta(days=i)) for i in range(30)]
    
    daily_revenue = []
    for date in dates:
        revenue = Bill.objects.filter(
            hospital=hospital, status='PAID', created_at__date=date
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        daily_revenue.append({
            'date': date.strftime('%Y-%m-%d'),
            'revenue': float(revenue)
        })
    
    data = {
        'daily_revenue': daily_revenue,
        'total_revenue': sum([d['revenue'] for d in daily_revenue]),
        'average_daily': sum([d['revenue'] for d in daily_revenue]) / len(daily_revenue)
    }
    
    return JsonResponse(data)
