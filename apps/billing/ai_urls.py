# apps/billing/ai_urls.py
"""
URL Configuration for AI-Enhanced Billing Features
"""

from django.urls import path
from . import ai_views

app_name = 'ai_billing'

urlpatterns = [
    # AI Billing Dashboard
    path('ai/dashboard/', ai_views.AIBillingDashboardView.as_view(), name='ai_dashboard'),
    
    # AI Invoice Generation
    path('ai/generate-invoice/', ai_views.AIInvoiceGeneratorView.as_view(), name='ai_generate_invoice'),
    
    # AI Invoice Optimization
    path('ai/optimize-invoice/', ai_views.AIInvoiceOptimizationView.as_view(), name='ai_optimize_invoice'),
    
    # AI Revenue Analytics
    path('ai/revenue-analytics/', ai_views.AIRevenueAnalyticsView.as_view(), name='ai_revenue_analytics'),
    
    # AI Payment Risk Management
    path('ai/payment-risks/', ai_views.AIPaymentRiskView.as_view(), name='ai_payment_risks'),
    
    # API Endpoints for AJAX calls
    path('api/unbilled-appointments/', ai_views.UnbilledAppointmentsAPIView.as_view(), name='api_unbilled_appointments'),
    path('api/ai-insights/', ai_views.AIInsightsAPIView.as_view(), name='api_ai_insights'),
    path('api/revenue-forecast/', ai_views.RevenueForecastAPIView.as_view(), name='api_revenue_forecast'),
    path('api/payment-predictions/', ai_views.PaymentPredictionsAPIView.as_view(), name='api_payment_predictions'),
]
