# apps/billing/ai_views.py
"""
AI-Enhanced Billing Views with Intelligent Automation
"""

import json
import logging
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View, TemplateView, ListView, DetailView, CreateView
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Sum, Avg, Count
from django.core.paginator import Paginator

from .models import (
    Invoice, InvoiceItem, MedicalService, Payment, InsuranceClaim,
    BillingAIInsights, RevenueAnalytics, PaymentRiskAssessment
)
from .ai_billing_engine import BillingAutomationEngine
from apps.appointments.models import Appointment
from apps.patients.models import Patient
# from tenants.permissions import  # Temporarily commented TenantFilterMixin

logger = logging.getLogger(__name__)


class AIBillingDashboardView(TemplateView):
    """
    AI-powered billing dashboard with revenue insights and automation metrics
    """
    template_name = 'billing/ai_billing_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            # Initialize AI billing engine
            billing_engine = BillingAutomationEngine(str(self.request.tenant.id))
            
            # Get billing overview metrics
            billing_metrics = self._get_billing_metrics()
            
            # Get AI insights and recommendations
            ai_insights = self._get_ai_insights()
            
            # Get revenue analytics
            revenue_analytics = self._get_revenue_analytics()
            
            # Get high-risk payment alerts
            payment_risks = self._get_payment_risk_alerts()
            
            # Get automation opportunities
            automation_opportunities = self._get_automation_opportunities()
            
            context.update({
                'billing_metrics': billing_metrics,
                'ai_insights': ai_insights,
                'revenue_analytics': revenue_analytics,
                'payment_risks': payment_risks,
                'automation_opportunities': automation_opportunities,
                'dashboard_active': True
            })
            
        except Exception as e:
            logger.error(f"Error loading AI billing dashboard: {str(e)}")
            context.update({
                'error': 'Unable to load AI billing dashboard data',
                'dashboard_active': True
            })
            
        return context
    
    def _get_billing_metrics(self):
        """Calculate key billing performance metrics"""
        try:
            today = timezone.now().date()
            week_ago = today - timedelta(days=7)
            month_ago = today - timedelta(days=30)
            
            # Revenue metrics
            total_revenue_month = Invoice.objects.filter(
                tenant=self.request.tenant,
                invoice_date__gte=month_ago,
                status__in=['PAID', 'PARTIALLY_PAID']
            ).aggregate(total=Sum('paid_amount'))['total'] or 0
            
            # Outstanding invoices
            outstanding_invoices = Invoice.objects.filter(
                tenant=self.request.tenant,
                status__in=['PENDING', 'OVERDUE', 'PARTIALLY_PAID']
            )
            outstanding_amount = outstanding_invoices.aggregate(
                total=Sum('balance_amount')
            )['total'] or 0
            
            # AI automation metrics
            ai_generated_invoices = Invoice.objects.filter(
                tenant=self.request.tenant,
                ai_generated=True,
                created_at__gte=month_ago
            ).count()
            
            total_invoices_month = Invoice.objects.filter(
                tenant=self.request.tenant,
                created_at__gte=month_ago
            ).count()
            
            automation_rate = (ai_generated_invoices / max(total_invoices_month, 1)) * 100
            
            # Collection efficiency
            collection_rate = self._calculate_collection_rate(month_ago)
            
            return {
                'total_revenue_month': float(total_revenue_month),
                'outstanding_amount': float(outstanding_amount),
                'outstanding_count': outstanding_invoices.count(),
                'automation_rate': round(automation_rate, 1),
                'collection_rate': round(collection_rate, 1),
                'ai_generated_invoices': ai_generated_invoices,
                'avg_payment_time': self._calculate_avg_payment_time(),
                'payment_success_rate': self._calculate_payment_success_rate()
            }
            
        except Exception as e:
            logger.error(f"Error calculating billing metrics: {str(e)}")
            return {
                'total_revenue_month': 0,
                'outstanding_amount': 0,
                'outstanding_count': 0,
                'automation_rate': 0,
                'collection_rate': 0,
                'ai_generated_invoices': 0,
                'avg_payment_time': 0,
                'payment_success_rate': 0
            }
    
    def _get_ai_insights(self):
        """Get recent AI billing insights"""
        try:
            insights = BillingAIInsights.objects.filter(
                tenant=self.request.tenant,
                is_implemented=False
            ).order_by('-implementation_priority', '-created_at')[:10]
            
            return [{
                'id': insight.id,
                'type': insight.insight_type,
                'title': insight.title,
                'description': insight.description,
                'confidence': insight.confidence_score,
                'priority': insight.implementation_priority,
                'potential_impact': float(insight.potential_revenue_impact or 0),
                'created_at': insight.created_at.isoformat()
            } for insight in insights]
            
        except Exception as e:
            logger.error(f"Error getting AI insights: {str(e)}")
            return []
    
    def _get_revenue_analytics(self):
        """Get revenue analytics and forecasting"""
        try:
            # Get latest monthly analytics
            latest_analytics = RevenueAnalytics.objects.filter(
                tenant=self.request.tenant,
                period_type='MONTHLY'
            ).order_by('-period_start').first()
            
            if not latest_analytics:
                return {
                    'predicted_revenue': 0,
                    'confidence': 0,
                    'trend': 'stable',
                    'forecast_accuracy': 0
                }
            
            # Calculate trend
            previous_analytics = RevenueAnalytics.objects.filter(
                tenant=self.request.tenant,
                period_type='MONTHLY',
                period_start__lt=latest_analytics.period_start
            ).order_by('-period_start').first()
            
            trend = 'stable'
            if previous_analytics:
                if latest_analytics.predicted_revenue > previous_analytics.predicted_revenue * 1.05:
                    trend = 'increasing'
                elif latest_analytics.predicted_revenue < previous_analytics.predicted_revenue * 0.95:
                    trend = 'decreasing'
            
            return {
                'predicted_revenue': float(latest_analytics.predicted_revenue),
                'confidence': latest_analytics.ai_confidence,
                'trend': trend,
                'forecast_accuracy': latest_analytics.accuracy_score or 0,
                'period_start': latest_analytics.period_start.isoformat(),
                'period_end': latest_analytics.period_end.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting revenue analytics: {str(e)}")
            return {
                'predicted_revenue': 0,
                'confidence': 0,
                'trend': 'stable',
                'forecast_accuracy': 0
            }
    
    def _get_payment_risk_alerts(self):
        """Get high-risk payment alerts"""
        try:
            high_risk_assessments = PaymentRiskAssessment.objects.filter(
                tenant=self.request.tenant,
                overall_risk_level__in=['HIGH', 'VERY_HIGH'],
                invoice__status__in=['PENDING', 'OVERDUE']
            ).order_by('-risk_score')[:15]
            
            return [{
                'patient_name': assessment.patient.get_full_name(),
                'invoice_number': assessment.invoice.invoice_number if assessment.invoice else 'N/A',
                'risk_level': assessment.overall_risk_level,
                'risk_score': assessment.risk_score,
                'amount': float(assessment.invoice.balance_amount) if assessment.invoice else 0,
                'predicted_days': assessment.predicted_payment_days,
                'recommendations': assessment.collection_strategy_recommendations
            } for assessment in high_risk_assessments]
            
        except Exception as e:
            logger.error(f"Error getting payment risk alerts: {str(e)}")
            return []
    
    def _get_automation_opportunities(self):
        """Get AI automation opportunities"""
        try:
            # Find appointments without invoices that could be auto-billed
            unbilled_appointments = Appointment.objects.filter(
                tenant=self.request.tenant,
                status='COMPLETED',
                invoice__isnull=True,
                appointment_date__gte=timezone.now().date() - timedelta(days=30)
            ).count()
            
            # Find invoices that could benefit from AI optimization
            unoptimized_invoices = Invoice.objects.filter(
                tenant=self.request.tenant,
                ai_generated=False,
                status='DRAFT'
            ).count()
            
            return {
                'unbilled_appointments': unbilled_appointments,
                'unoptimized_invoices': unoptimized_invoices,
                'potential_automation_savings': unbilled_appointments * 15,  # Est. 15 minutes per invoice
                'ai_optimization_potential': unoptimized_invoices * 0.05  # Est. 5% savings
            }
            
        except Exception as e:
            logger.error(f"Error getting automation opportunities: {str(e)}")
            return {
                'unbilled_appointments': 0,
                'unoptimized_invoices': 0,
                'potential_automation_savings': 0,
                'ai_optimization_potential': 0
            }
    
    def _calculate_collection_rate(self, since_date):
        """Calculate collection rate for given period"""
        try:
            total_invoiced = Invoice.objects.filter(
                tenant=self.request.tenant,
                invoice_date__gte=since_date
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            total_collected = Invoice.objects.filter(
                tenant=self.request.tenant,
                invoice_date__gte=since_date
            ).aggregate(collected=Sum('paid_amount'))['collected'] or 0
            
            if total_invoiced > 0:
                return (total_collected / total_invoiced) * 100
            return 0
            
        except Exception:
            return 0
    
    def _calculate_avg_payment_time(self):
        """Calculate average payment time in days"""
        try:
            paid_invoices = Invoice.objects.filter(
                tenant=self.request.tenant,
                status='PAID',
                last_payment_date__isnull=False
            )
            
            total_days = 0
            count = 0
            
            for invoice in paid_invoices:
                if invoice.last_payment_date:
                    days = (invoice.last_payment_date.date() - invoice.invoice_date).days
                    total_days += days
                    count += 1
            
            return total_days / count if count > 0 else 0
            
        except Exception:
            return 0
    
    def _calculate_payment_success_rate(self):
        """Calculate payment success rate"""
        try:
            total_invoices = Invoice.objects.filter(
                tenant=self.request.tenant,
                invoice_date__gte=timezone.now().date() - timedelta(days=90)
            ).count()
            
            paid_invoices = Invoice.objects.filter(
                tenant=self.request.tenant,
                invoice_date__gte=timezone.now().date() - timedelta(days=90),
                status__in=['PAID', 'PARTIALLY_PAID']
            ).count()
            
            return (paid_invoices / max(total_invoices, 1)) * 100
            
        except Exception:
            return 0


class AIInvoiceGeneratorView(View):
    """
    AI-powered automatic invoice generation from appointments
    """
    
    def post(self, request, *args, **kwargs):
        """Generate invoice using AI automation"""
        try:
            appointment_id = request.POST.get('appointment_id')
            include_emr = request.POST.get('include_emr', 'true').lower() == 'true'
            
            if not appointment_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Appointment ID is required'
                })
            
            # Verify appointment exists and belongs to tenant
            try:
                appointment = Appointment.objects.get(
                    id=appointment_id,
                    tenant=request.tenant
                )
            except Appointment.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Appointment not found'
                })
            
            # Initialize AI billing engine
            billing_engine = BillingAutomationEngine(str(request.tenant.id))
            
            # Generate invoice using AI
            result = billing_engine.auto_generate_invoice_from_appointment(
                appointment_id, include_emr
            )
            
            if 'error' in result:
                return JsonResponse({
                    'success': False,
                    'error': result['error']
                })
            
            # Create invoice record with AI data
            with transaction.atomic():
                invoice = self._create_invoice_from_ai_result(
                    appointment, result, request.user
                )
                
                # Generate payment risk assessment
                self._create_payment_risk_assessment(invoice, billing_engine)
            
            return JsonResponse({
                'success': True,
                'invoice_id': str(invoice.id),
                'invoice_number': invoice.invoice_number,
                'total_amount': float(invoice.total_amount),
                'ai_confidence': result.get('confidence_score', 0),
                'services_identified': len(result.get('suggested_services', [])),
                'optimization_savings': float(result.get('pricing_analysis', {}).get('savings_amount', 0)),
                'redirect_url': f'/billing/invoices/{invoice.id}/'
            })
            
        except Exception as e:
            logger.error(f"Error in AI invoice generation: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'Invoice generation failed: {str(e)}'
            })
    
    def _create_invoice_from_ai_result(self, appointment, ai_result, user):
        """Create invoice from AI analysis result"""
        invoice_data = ai_result.get('invoice_data', {})
        
        # Create invoice
        invoice = Invoice.objects.create(
            tenant=appointment.tenant,
            patient=appointment.patient,
            appointment=appointment,
            invoice_date=timezone.now().date(),
            due_date=timezone.now().date() + timedelta(days=30),
            subtotal=invoice_data.get('subtotal', 0),
            tax_rate=invoice_data.get('tax_rate', 0.08),
            tax_amount=invoice_data.get('tax_amount', 0),
            total_amount=invoice_data.get('total_amount', 0),
            balance_amount=invoice_data.get('total_amount', 0),
            ai_generated=True,
            ai_confidence_score=ai_result.get('confidence_score', 0),
            ai_pricing_optimization=ai_result.get('pricing_analysis', {}),
            ai_revenue_insights=ai_result.get('ai_recommendations', {}),
            created_by=user,
            status='DRAFT'
        )
        
        # Create invoice items
        for service in ai_result.get('suggested_services', []):
            InvoiceItem.objects.create(
                invoice=invoice,
                service_code=service.get('code', ''),
                description=service.get('name', ''),
                quantity=service.get('quantity', 1),
                unit_price=service.get('base_price', 0),
                total_amount=service.get('quantity', 1) * service.get('base_price', 0),
                ai_generated=True,
                ai_confidence=service.get('ai_confidence', 0),
                ai_source=service.get('source', ''),
                ai_extraction_details=service.get('extracted_from', {})
            )
        
        return invoice
    
    def _create_payment_risk_assessment(self, invoice, billing_engine):
        """Create AI payment risk assessment for invoice"""
        try:
            prediction = billing_engine.predict_payment_likelihood(
                {'total_amount': float(invoice.total_amount)},
                invoice.patient
            )
            
            # Determine risk level from probability
            risk_level = 'VERY_LOW'
            if prediction['payment_probability'] < 0.3:
                risk_level = 'VERY_HIGH'
            elif prediction['payment_probability'] < 0.5:
                risk_level = 'HIGH'
            elif prediction['payment_probability'] < 0.7:
                risk_level = 'MEDIUM'
            elif prediction['payment_probability'] < 0.9:
                risk_level = 'LOW'
            
            PaymentRiskAssessment.objects.create(
                tenant=invoice.tenant,
                patient=invoice.patient,
                invoice=invoice,
                overall_risk_level=risk_level,
                risk_score=1 - prediction['payment_probability'],
                payment_probability=prediction['payment_probability'],
                predicted_payment_days=prediction['predicted_payment_days'],
                payment_behavior_category=prediction.get('factors', {}).get('patient_category', 'AVERAGE').upper(),
                risk_factors=prediction.get('factors', {}),
                collection_strategy_recommendations=prediction.get('recommendations', []),
                confidence_score=prediction.get('confidence_score', 0.8)
            )
            
        except Exception as e:
            logger.error(f"Error creating payment risk assessment: {str(e)}")


class AIInvoiceOptimizationView(View):
    """
    AI-powered invoice optimization and pricing analysis
    """
    
    def post(self, request, *args, **kwargs):
        """Optimize existing invoice using AI"""
        try:
            invoice_id = request.POST.get('invoice_id')
            
            if not invoice_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Invoice ID is required'
                })
            
            # Get invoice
            try:
                invoice = Invoice.objects.get(
                    id=invoice_id,
                    tenant=request.tenant,
                    status='DRAFT'  # Only optimize draft invoices
                )
            except Invoice.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Invoice not found or cannot be optimized'
                })
            
            # Initialize AI billing engine
            billing_engine = BillingAutomationEngine(str(request.tenant.id))
            
            # Get current invoice items as services
            current_services = []
            for item in invoice.items.all():
                current_services.append({
                    'code': item.service_code,
                    'name': item.description,
                    'base_price': float(item.unit_price),
                    'quantity': item.quantity
                })
            
            # AI pricing optimization
            optimization = billing_engine._optimize_pricing(
                current_services, invoice.patient, invoice.appointment
            )
            
            # Calculate new totals if optimization applied
            original_total = float(invoice.total_amount)
            optimized_total = optimization.get('optimized_total', original_total)
            savings = optimization.get('savings_amount', 0)
            
            # Update invoice with optimization
            if savings > 0:
                invoice.ai_pricing_optimization = optimization
                
                # Apply optimization to invoice totals
                invoice.subtotal = optimized_total / (1 + float(invoice.tax_rate))
                invoice.tax_amount = invoice.subtotal * float(invoice.tax_rate)
                invoice.total_amount = optimized_total
                invoice.balance_amount = optimized_total
                
                invoice.save()
                
                # Update items with optimized pricing if needed
                self._apply_item_optimization(invoice, optimization)
            
            return JsonResponse({
                'success': True,
                'original_amount': original_total,
                'optimized_amount': optimized_total,
                'savings': float(savings),
                'optimization_factors': optimization.get('optimization_factors', []),
                'pricing_strategy': optimization.get('pricing_strategy', 'standard')
            })
            
        except Exception as e:
            logger.error(f"Error in AI invoice optimization: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'Optimization failed: {str(e)}'
            })
    
    def _apply_item_optimization(self, invoice, optimization):
        """Apply optimization to individual invoice items"""
        try:
            # Apply proportional discount to items if overall discount was applied
            discount_factor = optimization.get('optimized_total', 0) / optimization.get('original_total', 1)
            
            if discount_factor < 1.0:  # Discount was applied
                for item in invoice.items.all():
                    original_price = item.unit_price
                    item.original_price = original_price
                    item.unit_price = original_price * discount_factor
                    item.total_amount = item.quantity * item.unit_price
                    item.pricing_optimization_applied = True
                    item.save()
                    
        except Exception as e:
            logger.error(f"Error applying item optimization: {str(e)}")


class AIRevenueAnalyticsView(TemplateView):
    """
    AI-powered revenue analytics and forecasting dashboard
    """
    template_name = 'billing/ai_revenue_analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            # Get revenue analytics data
            revenue_data = self._get_revenue_analytics_data()
            
            # Get forecasting data
            forecast_data = self._get_forecast_data()
            
            # Get performance metrics
            performance_metrics = self._get_performance_metrics()
            
            # Get optimization opportunities
            optimization_opportunities = self._get_optimization_opportunities()
            
            context.update({
                'revenue_data': revenue_data,
                'forecast_data': forecast_data,
                'performance_metrics': performance_metrics,
                'optimization_opportunities': optimization_opportunities
            })
            
        except Exception as e:
            logger.error(f"Error loading revenue analytics: {str(e)}")
            context['error'] = 'Unable to load revenue analytics data'
        
        return context
    
    def _get_revenue_analytics_data(self):
        """Get comprehensive revenue analytics"""
        # Implementation would include detailed revenue analysis
        return {}
    
    def _get_forecast_data(self):
        """Get AI revenue forecasting data"""
        # Implementation would include AI forecasting
        return {}
    
    def _get_performance_metrics(self):
        """Get AI performance metrics"""
        # Implementation would include AI performance tracking
        return {}
    
    def _get_optimization_opportunities(self):
        """Get AI-identified optimization opportunities"""
        # Implementation would include optimization recommendations
        return {}


class AIPaymentRiskView(ListView):
    """
    AI-powered payment risk assessment and management
    """
    model = PaymentRiskAssessment
    template_name = 'billing/ai_payment_risk.html'
    context_object_name = 'risk_assessments'
    paginate_by = 20
    
    def get_queryset(self):
        return PaymentRiskAssessment.objects.filter(
            tenant=self.request.tenant
        ).order_by('-risk_score', '-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add risk summary statistics
        context['risk_summary'] = self._get_risk_summary()
        return context
    
    def _get_risk_summary(self):
        """Get payment risk summary statistics"""
        try:
            assessments = PaymentRiskAssessment.objects.filter(
                tenant=self.request.tenant
            )
            
            total_assessments = assessments.count()
            high_risk_count = assessments.filter(
                overall_risk_level__in=['HIGH', 'VERY_HIGH']
            ).count()
            
            avg_risk_score = assessments.aggregate(
                avg_score=Avg('risk_score')
            )['avg_score'] or 0
            
            total_at_risk = assessments.filter(
                overall_risk_level__in=['HIGH', 'VERY_HIGH'],
                invoice__isnull=False
            ).aggregate(
                total=Sum('invoice__balance_amount')
            )['total'] or 0
            
            return {
                'total_assessments': total_assessments,
                'high_risk_count': high_risk_count,
                'high_risk_percentage': (high_risk_count / max(total_assessments, 1)) * 100,
                'avg_risk_score': round(avg_risk_score, 3),
                'total_at_risk_amount': float(total_at_risk)
            }
            
        except Exception as e:
            logger.error(f"Error calculating risk summary: {str(e)}")
            return {
                'total_assessments': 0,
                'high_risk_count': 0,
                'high_risk_percentage': 0,
                'avg_risk_score': 0,
                'total_at_risk_amount': 0
            }


class UnbilledAppointmentsAPIView(View):
    """
    API view to get unbilled appointments for AI invoice generation
    """
    
    def get(self, request, *args, **kwargs):
        """Get list of unbilled appointments"""
        try:
            # Get completed appointments without invoices
            unbilled_appointments = Appointment.objects.filter(
                tenant=request.tenant,
                status='COMPLETED',
                invoice__isnull=True,
                appointment_date__gte=timezone.now().date() - timedelta(days=90)
            ).select_related('patient', 'doctor').order_by('-appointment_date')[:50]
            
            appointments_data = []
            for appointment in unbilled_appointments:
                appointments_data.append({
                    'id': str(appointment.id),
                    'patient_name': appointment.patient.get_full_name(),
                    'doctor_name': appointment.doctor.get_full_name() if appointment.doctor else 'N/A',
                    'date': appointment.appointment_date.strftime('%Y-%m-%d'),
                    'time': appointment.appointment_time.strftime('%H:%M') if appointment.appointment_time else 'N/A',
                    'department': appointment.department.name if appointment.department else 'General'
                })
            
            return JsonResponse({
                'success': True,
                'appointments': appointments_data,
                'count': len(appointments_data)
            })
            
        except Exception as e:
            logger.error(f"Error getting unbilled appointments: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Unable to load unbilled appointments'
            })


class AIInsightsAPIView(View):
    """
    API view for AI billing insights and recommendations
    """
    
    def get(self, request, *args, **kwargs):
        """Get AI billing insights"""
        try:
            insights = BillingAIInsights.objects.filter(
                tenant=request.tenant,
                is_implemented=False
            ).order_by('-implementation_priority', '-created_at')[:20]
            
            insights_data = []
            for insight in insights:
                insights_data.append({
                    'id': str(insight.id),
                    'type': insight.insight_type,
                    'title': insight.title,
                    'description': insight.description,
                    'confidence': insight.confidence_score,
                    'priority': insight.implementation_priority,
                    'potential_impact': float(insight.potential_revenue_impact or 0),
                    'created_at': insight.created_at.isoformat()
                })
            
            return JsonResponse({
                'success': True,
                'insights': insights_data,
                'count': len(insights_data)
            })
            
        except Exception as e:
            logger.error(f"Error getting AI insights: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Unable to load AI insights'
            })
    
    def post(self, request, *args, **kwargs):
        """Implement or dismiss an AI insight"""
        try:
            insight_id = request.POST.get('insight_id')
            action = request.POST.get('action')  # 'implement' or 'dismiss'
            
            insight = get_object_or_404(BillingAIInsights, id=insight_id, tenant=request.tenant)
            
            if action == 'implement':
                insight.is_implemented = True
                insight.implemented_at = timezone.now()
                insight.implemented_by = request.user
                message = 'AI insight implemented successfully'
            elif action == 'dismiss':
                insight.is_dismissed = True
                insight.dismissed_at = timezone.now()
                insight.dismissed_by = request.user
                message = 'AI insight dismissed'
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid action'
                })
            
            insight.save()
            
            return JsonResponse({
                'success': True,
                'message': message
            })
            
        except Exception as e:
            logger.error(f"Error processing AI insight action: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Unable to process insight action'
            })


class RevenueForecastAPIView(View):
    """
    API view for revenue forecasting data
    """
    
    def get(self, request, *args, **kwargs):
        """Get revenue forecast data for charts"""
        try:
            # Get historical revenue data
            historical_data = self._get_historical_revenue_data()
            
            # Get AI predictions
            forecast_data = self._get_forecast_predictions()
            
            return JsonResponse({
                'success': True,
                'historical': historical_data,
                'forecast': forecast_data,
                'accuracy_metrics': self._get_forecast_accuracy()
            })
            
        except Exception as e:
            logger.error(f"Error getting revenue forecast: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Unable to load revenue forecast data'
            })
    
    def _get_historical_revenue_data(self):
        """Get historical revenue data for the last 12 months"""
        try:
            months = []
            revenues = []
            
            for i in range(12, 0, -1):
                month_start = timezone.now().replace(day=1) - timedelta(days=30 * i)
                month_end = month_start.replace(day=28) + timedelta(days=4)
                month_end = month_end - timedelta(days=month_end.day)
                
                revenue = Invoice.objects.filter(
                    tenant=self.request.tenant,
                    invoice_date__gte=month_start.date(),
                    invoice_date__lte=month_end.date(),
                    status__in=['PAID', 'PARTIALLY_PAID']
                ).aggregate(total=Sum('paid_amount'))['total'] or 0
                
                months.append(month_start.strftime('%b %Y'))
                revenues.append(float(revenue))
            
            return {
                'months': months,
                'revenues': revenues
            }
            
        except Exception:
            return {'months': [], 'revenues': []}
    
    def _get_forecast_predictions(self):
        """Get AI forecast predictions"""
        try:
            # Get recent predictions
            predictions = RevenueAnalytics.objects.filter(
                tenant=self.request.tenant,
                period_type='MONTHLY',
                period_start__gte=timezone.now().date()
            ).order_by('period_start')[:6]
            
            forecast_months = []
            forecast_revenues = []
            
            for prediction in predictions:
                forecast_months.append(prediction.period_start.strftime('%b %Y'))
                forecast_revenues.append(float(prediction.predicted_revenue))
            
            return {
                'months': forecast_months,
                'revenues': forecast_revenues
            }
            
        except Exception:
            return {'months': [], 'revenues': []}
    
    def _get_forecast_accuracy(self):
        """Get forecast accuracy metrics"""
        try:
            recent_analytics = RevenueAnalytics.objects.filter(
                tenant=self.request.tenant,
                accuracy_score__isnull=False
            ).order_by('-created_at')[:10]
            
            if recent_analytics.exists():
                avg_accuracy = recent_analytics.aggregate(
                    avg=Avg('accuracy_score')
                )['avg'] or 0
                
                return {
                    'average_accuracy': round(avg_accuracy, 2),
                    'samples': recent_analytics.count()
                }
            
            return {'average_accuracy': 0, 'samples': 0}
            
        except Exception:
            return {'average_accuracy': 0, 'samples': 0}


class PaymentPredictionsAPIView(View):
    """
    API view for payment prediction analytics
    """
    
    def get(self, request, *args, **kwargs):
        """Get payment prediction analytics"""
        try:
            # Get payment risk distribution
            risk_distribution = self._get_risk_distribution()
            
            # Get payment timeline predictions
            payment_timeline = self._get_payment_timeline()
            
            # Get collection recommendations
            recommendations = self._get_collection_recommendations()
            
            return JsonResponse({
                'success': True,
                'risk_distribution': risk_distribution,
                'payment_timeline': payment_timeline,
                'recommendations': recommendations
            })
            
        except Exception as e:
            logger.error(f"Error getting payment predictions: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Unable to load payment prediction data'
            })
    
    def _get_risk_distribution(self):
        """Get distribution of payment risk levels"""
        try:
            risk_counts = PaymentRiskAssessment.objects.filter(
                tenant=self.request.tenant
            ).values('overall_risk_level').annotate(
                count=Count('id')
            ).order_by('overall_risk_level')
            
            distribution = {}
            for item in risk_counts:
                distribution[item['overall_risk_level']] = item['count']
            
            return distribution
            
        except Exception:
            return {}
    
    def _get_payment_timeline(self):
        """Get predicted payment timeline"""
        try:
            # Group by predicted payment days
            timeline_data = PaymentRiskAssessment.objects.filter(
                tenant=self.request.tenant,
                invoice__status__in=['PENDING', 'OVERDUE']
            ).values('predicted_payment_days').annotate(
                count=Count('id'),
                total_amount=Sum('invoice__balance_amount')
            ).order_by('predicted_payment_days')
            
            timeline = []
            for item in timeline_data:
                timeline.append({
                    'days': item['predicted_payment_days'],
                    'count': item['count'],
                    'amount': float(item['total_amount'] or 0)
                })
            
            return timeline
            
        except Exception:
            return []
    
    def _get_collection_recommendations(self):
        """Get AI collection strategy recommendations"""
        try:
            # Get high-priority collection cases
            high_priority = PaymentRiskAssessment.objects.filter(
                tenant=self.request.tenant,
                overall_risk_level__in=['HIGH', 'VERY_HIGH'],
                invoice__status__in=['PENDING', 'OVERDUE']
            ).order_by('-risk_score')[:10]
            
            recommendations = []
            for assessment in high_priority:
                if assessment.collection_strategy_recommendations:
                    recommendations.append({
                        'patient': assessment.patient.get_full_name(),
                        'invoice': assessment.invoice.invoice_number if assessment.invoice else 'N/A',
                        'amount': float(assessment.invoice.balance_amount) if assessment.invoice else 0,
                        'risk_level': assessment.overall_risk_level,
                        'strategies': assessment.collection_strategy_recommendations
                    })
            
            return recommendations
            
        except Exception:
            return []
