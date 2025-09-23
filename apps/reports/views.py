# apps/reports/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from apps.core.mixins import UnifiedSystemMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
# from apps.accounts.models import CustomUser as User
from apps.patients.models import Patient
from apps.appointments.models import Appointment
from apps.billing.models import Bill
from apps.emergency.models import EmergencyCase
from .models import Report, ReportTemplate
from .forms import ReportGenerationForm, ReportTemplateForm
import json

# Test endpoint for financial data (temporary - remove after testing)
def test_financial_report(request):
    """Test financial report without authentication"""
    today = timezone.now().date()
    dates = [(today - timedelta(days=i)) for i in range(30)]
    
    daily_revenue = []
    for i, date in enumerate(dates):
        # Using dummy data for testing since we may not have bills in the database
        daily_revenue.append({
            'date': date.strftime('%Y-%m-%d'),
            'revenue': float(100.50 * (i + 1))  # Dummy revenue data
        })
    
    total_revenue = sum([d['revenue'] for d in daily_revenue])
    average_daily = total_revenue / len(daily_revenue) if daily_revenue else 0
    
    data = {
        'daily_revenue': daily_revenue,
        'total_revenue': total_revenue,
        'average_daily': average_daily,
        'pending_bills': 1250.75,  # Dummy pending bills
    }
    
    return JsonResponse(data)

class ReportListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all reports"""
    model = Report
    template_name = 'reports/report_list.html'
    context_object_name = 'reports'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.has_module_permission('reports')
    
    def get_queryset(self):
        try:
            # Check if the table exists before trying to query
            from django.db import connection
            table_names = connection.introspection.table_names()
            if 'reports_report' not in table_names:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning("Report table does not exist, returning empty queryset")
                return self.model.objects.none()
            
            # Unified system - filter by status instead of is_active
            return Report.objects.exclude(status='deleted').order_by('-created_at')
        except Exception as e:
            # Handle case where reports tables don't exist
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error accessing reports data: {e}")
            return self.model.objects.none()
    
    def get_context_data(self, **kwargs):
        try:
            # Check if tables exist before querying
            from django.db import connection
            table_names = connection.introspection.table_names()
            
            if 'reports_report' not in table_names:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning("Reports tables do not exist, using empty context")
                
                # Set object_list to empty for ListView to work properly
                if not hasattr(self, 'object_list'):
                    self.object_list = self.get_queryset()
                
                # Return minimal context to prevent crashes
                context = super().get_context_data(**kwargs)
                context.update({
                    'total_reports': 0,
                    'recent_reports': [],
                    'report_types': [],
                })
                return context
            
            context = super().get_context_data(**kwargs)
            
            # Get statistics for unified system
            try:
                all_reports = Report.objects.exclude(status='deleted')
                context.update({
                    'total_reports': all_reports.count(),
                    'recent_reports': all_reports.order_by('-created_at')[:5],
                })
            except Exception:
                context.update({
                    'total_reports': 0,
                    'recent_reports': [],
                })
            
            return context
        except Exception as e:
            # Handle case where reports tables don't exist
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error getting reports context data: {e}")
            
            # Set object_list to empty for ListView to work properly
            if not hasattr(self, 'object_list'):
                self.object_list = self.get_queryset()
            
            # Return minimal context to prevent crashes
            context = super().get_context_data(**kwargs)
            context.update({
                'total_reports': 0,
                'recent_reports': [],
                'report_types': [],
            })
            return context


class GenerateReportView(UnifiedSystemMixin, LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Generate new report"""
    model = Report
    form_class = ReportGenerationForm
    template_name = 'reports/generate_report.html'
    success_url = reverse_lazy('reports:report_list')
    
    def test_func(self):
        return self.request.user.has_module_permission('reports')
    
    def get_context_data(self, **kwargs):
        try:
            # Check if tables exist before loading form
            from django.db import connection
            table_names = connection.introspection.table_names()
            
            if 'reports_report' not in table_names:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning("Reports tables do not exist, report generation unavailable")
                
                context = super().get_context_data(**kwargs)
                context['tables_missing'] = True
                context['error_message'] = 'Report generation is currently unavailable. Please contact your administrator.'
                return context
            
            return super().get_context_data(**kwargs)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error in report generation view: {e}")
            
            context = super().get_context_data(**kwargs)
            context['tables_missing'] = True
            context['error_message'] = 'Report generation is currently unavailable. Please contact your administrator.'
            return context
    
    def form_valid(self, form):
        try:
            # Check if tables exist before saving
            from django.db import connection
            table_names = connection.introspection.table_names()
            
            if 'reports_report' not in table_names:
                messages.error(self.request, 'Report generation is currently unavailable. Please contact your administrator.')
                return self.form_invalid(form)
            
            # Unified system - no tenant reference needed
            form.instance.generated_by = self.request.user
            form.instance.status = 'completed'
            
            # Save to default database
            self.object = form.save()
            
            messages.success(self.request, 'Report generation started. You will be notified when ready.')
            return redirect(self.get_success_url())
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating report: {e}")
            messages.error(self.request, 'Error generating report. Please try again.')
            return self.form_invalid(form)


class ReportDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """View report details"""
    model = Report
    template_name = 'reports/report_detail.html'
    context_object_name = 'report'
    
    def test_func(self):
        return self.request.user.has_module_permission('reports')
    
    def get_queryset(self):
        try:
            # Check if the table exists before trying to query
            from django.db import connection
            table_names = connection.introspection.table_names()
            if 'reports_report' not in table_names:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning("Report table does not exist, returning empty queryset")
                return self.model.objects.none()
            
            # Unified system - filter by status
            return Report.objects.exclude(status='deleted')
        except Exception as e:
            # Handle case where reports tables don't exist
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error accessing reports data: {e}")
            return self.model.objects.none()


class ReportTemplateListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List report templates"""
    model = ReportTemplate
    template_name = 'reports/template_list.html'
    context_object_name = 'templates'
    
    def test_func(self):
        return self.request.user.has_module_permission('reports')
    
    def get_queryset(self):
        try:
            # Check if the table exists before trying to query
            from django.db import connection
            table_names = connection.introspection.table_names()
            if 'reports_reporttemplate' not in table_names:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning("ReportTemplate table does not exist, returning empty queryset")
                return self.model.objects.none()
            
            tenant = self.request.user.tenant
            if tenant:
                return ReportTemplate.objects.filter(tenant=tenant, is_active=True)
            return ReportTemplate.objects.none()
        except Exception as e:
            # Handle case where reports tables don't exist
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error accessing report template data: {e}")
            return self.model.objects.none()


class ReportTemplateCreateView(UnifiedSystemMixin, LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create report template"""
    model = ReportTemplate
    form_class = ReportTemplateForm
    template_name = 'reports/template_form.html'
    success_url = reverse_lazy('reports:template_list')
    
    def test_func(self):
        return self.request.user.role in ['ADMIN', 'SUPERADMIN'] or self.request.user.is_superuser
    
    def form_valid(self, form):
        tenant = self.request.user.tenant
        
        # If no tenant is set (superuser case), try to get from user
        if not tenant and self.request.user.tenant:
            tenant = self.request.user.tenant
        elif not tenant:
            # For superusers without a default tenant, we need to handle this
            # For now, let's try to get the first tenant or create a default one
            if not tenant:
                # This case should ideally not happen in production
                # but as a fallback for development:
                raise Exception("No tenants found. Please create a tenant first.")
        
        form.instance.tenant = tenant
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
    tenant = request.user.tenant
    report = get_object_or_404(Report, pk=pk, tenant=tenant)
    
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
        tenant = request.user.tenant
        report = get_object_or_404(Report, pk=pk, tenant=tenant)
        report.delete()
        messages.success(request, 'Report deleted successfully.')
    
    return redirect('reports:report_list')


@login_required
def use_template(request, pk):
    """Use template to generate report"""
    tenant = request.user.tenant
    template = get_object_or_404(ReportTemplate, pk=pk, tenant=tenant)
    
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
    tenant = request.user.tenant
    
    # Get date range
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    data = {
        'total_patients': Patient.objects.filter(tenant=tenant).count(),
        'new_this_week': Patient.objects.filter(
            tenant=tenant, created_at__date__gte=week_ago
        ).count(),
        'new_this_month': Patient.objects.filter(
            tenant=tenant, created_at__date__gte=month_ago
        ).count(),
        'by_gender': Patient.objects.filter(tenant=tenant).values('gender').annotate(
            count=Count('id')
        ),
        'by_blood_group': Patient.objects.filter(tenant=tenant).values('blood_group').annotate(
            count=Count('id')
        )
    }
    
    return JsonResponse(data)


@login_required
def appointments_report(request):
    """Quick appointments report"""
    tenant = request.user.tenant
    
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    data = {
        'total_appointments': Appointment.objects.filter(tenant=tenant).count(),
        'this_week': Appointment.objects.filter(
            tenant=tenant, appointment_date__gte=week_ago
        ).count(),
        'today': Appointment.objects.filter(
            tenant=tenant, appointment_date=today
        ).count(),
        'by_status': Appointment.objects.filter(tenant=tenant).values('status').annotate(
            count=Count('id')
        ),
        'by_type': Appointment.objects.filter(tenant=tenant).values('appointment_type').annotate(
            count=Count('id')
        )
    }
    
    return JsonResponse(data)


@login_required
def billing_report(request):
    """Quick billing report"""
    tenant = request.user.tenant
    
    today = timezone.now().date()
    month_ago = today - timedelta(days=30)
    
    data = {
        'total_bills': Bill.objects.filter(tenant=tenant).count(),
        'total_revenue': Bill.objects.filter(
            tenant=tenant, status='PAID'
        ).aggregate(total=Sum('total_amount'))['total'] or 0,
        'this_month_revenue': Bill.objects.filter(
            tenant=tenant, status='PAID', created_at__date__gte=month_ago
        ).aggregate(total=Sum('total_amount'))['total'] or 0,
        'pending_amount': Bill.objects.filter(
            tenant=tenant, status='PENDING'
        ).aggregate(total=Sum('total_amount'))['total'] or 0,
        'by_status': Bill.objects.filter(tenant=tenant).values('status').annotate(
            count=Count('id')
        )
    }
    
    return JsonResponse(data)


@login_required
def financial_dashboard(request):
    """Financial reports dashboard page"""
    return render(request, 'reports/financial_dashboard.html')


@login_required
def financial_report(request):
    """Quick financial report API"""
    # Get hospital from session for hospital admin
    selected_hospital_id = request.session.get('selected_hospital_id')
    
    if not selected_hospital_id:
        return JsonResponse({'error': 'No hospital selected'}, status=400)
    
    today = timezone.now().date()
    dates = [(today - timedelta(days=i)) for i in range(30)]
    
    daily_revenue = []
    for date in dates:
        revenue = Bill.objects.filter(
            patient__hospital_id=selected_hospital_id, 
            status='PAID', 
            created_at__date=date
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        daily_revenue.append({
            'date': date.strftime('%Y-%m-%d'),
            'revenue': float(revenue)
        })
    
    # Calculate additional financial metrics
    total_revenue = sum([d['revenue'] for d in daily_revenue])
    average_daily = total_revenue / len(daily_revenue) if daily_revenue else 0
    
    # Get pending bills
    pending_bills = Bill.objects.filter(
        patient__hospital_id=selected_hospital_id, 
        status='PENDING'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    data = {
        'daily_revenue': daily_revenue,
        'total_revenue': total_revenue,
        'average_daily': average_daily,
        'pending_bills': float(pending_bills),
    }
    
    return JsonResponse(data)


@login_required
def doctor_performance_report(request):
    """Doctor performance summary report"""
    # Simple placeholder - can be enhanced later
    return render(request, 'reports/doctor_performance.html', {
        'title': 'Doctor Performance Report',
        'message': 'Doctor performance reporting will be available soon.',
    })


@login_required
def inventory_summary_report(request):
    """Inventory summary report"""
    # Simple placeholder - can be enhanced later  
    return render(request, 'reports/inventory_summary.html', {
        'title': 'Inventory Summary Report',
        'message': 'Inventory reporting will be available soon.',
    })


@login_required
def lab_summary_report(request):
    """Lab summary report"""
    # Simple placeholder - can be enhanced later
    return render(request, 'reports/lab_summary.html', {
        'title': 'Lab Summary Report', 
        'message': 'Lab reporting will be available soon.',
    })


@login_required
def patient_summary_report(request):
    """Patient summary report"""
    # Simple placeholder - can be enhanced later
    return render(request, 'reports/patient_summary.html', {
        'title': 'Patient Summary Report',
        'message': 'Patient analytics will be available soon.',
    })
