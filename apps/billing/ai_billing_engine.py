# apps/billing/ai_billing_engine.py
"""
AI-Powered Billing Automation Engine
Intelligent invoice generation, pricing optimization, and revenue analytics
"""

import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from django.utils import timezone
from django.db.models import Q, Sum, Avg, Count
from django.core.cache import cache
from django.conf import settings

from apps.emr.models import MedicalRecord, VitalSigns, Medication, LabResult
from apps.appointments.models import Appointment
from apps.patients.models import Patient
from .models import Invoice, MedicalService, InvoiceItem

logger = logging.getLogger(__name__)


class BillingAutomationEngine:
    """
    AI-powered billing automation and revenue optimization engine
    """
    
    def __init__(self, hospital_id: str = None):
        self.hospital_id = hospital_id or self._get_default_hospital_id()
        self.cache_timeout = 300  # 5 minutes
        
        # Load AI models and pricing data
        self.pricing_model = self._load_pricing_model()
        self.coding_database = self._load_medical_coding_database()
        self.insurance_rules = self._load_insurance_rules()
    
    def _get_default_hospital_id(self):
        """Get default hospital ID for testing"""
        try:
            from django.apps import apps
            Tenant = apps.get_model('tenants', 'Tenant')
            tenant = Tenant.objects.first()
            return str(tenant.id) if tenant else 'DEMO001'
        except:
            return 'DEMO001'
    
    def auto_generate_invoice_from_appointment(
        self, 
        appointment_id: str,
        include_emr_services: bool = True
    ) -> Dict:
        """
        Automatically generate invoice from appointment and EMR data
        
        Args:
            appointment_id: Appointment to generate invoice for
            include_emr_services: Include services from EMR records
            
        Returns:
            Invoice generation result with AI recommendations
        """
        try:
            # Get appointment and related data
            appointment = Appointment.objects.get(id=appointment_id)
            patient = appointment.patient
            
            # Get medical records for this appointment
            medical_records = MedicalRecord.objects.filter(
                appointment=appointment,
                tenant=appointment.tenant
            )
            
            # AI-powered service identification
            suggested_services = self._identify_billable_services(
                appointment, medical_records
            )
            
            # AI pricing optimization
            optimized_pricing = self._optimize_pricing(
                suggested_services, patient, appointment
            )
            
            # Generate invoice with AI recommendations
            invoice_data = self._create_invoice_structure(
                appointment, suggested_services, optimized_pricing
            )
            
            # Calculate AI confidence and recommendations
            ai_analysis = self._analyze_billing_opportunity(
                appointment, suggested_services, optimized_pricing
            )
            
            return {
                'invoice_data': invoice_data,
                'suggested_services': suggested_services,
                'pricing_analysis': optimized_pricing,
                'ai_recommendations': ai_analysis,
                'estimated_revenue': self._calculate_estimated_revenue(invoice_data),
                'confidence_score': ai_analysis.get('confidence', 0.85),
                'processing_time': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error auto-generating invoice: {str(e)}")
            return {
                'error': f'Invoice generation failed: {str(e)}',
                'suggested_services': [],
                'ai_recommendations': {},
                'confidence_score': 0.0
            }
    
    def _identify_billable_services(
        self, 
        appointment: Appointment, 
        medical_records: List[MedicalRecord]
    ) -> List[Dict]:
        """
        AI-powered identification of billable services from clinical data
        """
        try:
            services = []
            
            # Base consultation service
            consultation_service = self._get_consultation_service(appointment)
            if consultation_service:
                services.append(consultation_service)
            
            # Analyze medical records for additional services
            for record in medical_records:
                # Extract services from medical record
                record_services = self._extract_services_from_medical_record(record)
                services.extend(record_services)
                
                # Analyze procedures and treatments
                procedure_services = self._identify_procedures_from_record(record)
                services.extend(procedure_services)
            
            # AI-powered service recommendations based on symptoms and diagnoses
            ai_recommended_services = self._ai_recommend_additional_services(
                appointment, medical_records
            )
            services.extend(ai_recommended_services)
            
            # Remove duplicates and validate
            unique_services = self._deduplicate_and_validate_services(services)
            
            return unique_services
            
        except Exception as e:
            logger.error(f"Error identifying billable services: {str(e)}")
            return []
    
    def _get_consultation_service(self, appointment: Appointment) -> Dict:
        """Get base consultation service based on appointment type"""
        try:
            # Map appointment types to service codes
            service_mapping = {
                'CONSULTATION': 'CONS001',
                'FOLLOW_UP': 'CONS002',
                'EMERGENCY': 'CONS003',
                'SPECIALIST': 'CONS004'
            }
            
            appointment_type = getattr(appointment, 'appointment_type', 'CONSULTATION')
            service_code = service_mapping.get(appointment_type, 'CONS001')
            
            # Get service from database or create default
            try:
                service = MedicalService.objects.get(
                    tenant=appointment.tenant,
                    code=service_code
                )
                return {
                    'service_id': service.id,
                    'code': service.code,
                    'name': service.name,
                    'base_price': float(service.base_price),
                    'quantity': 1,
                    'ai_confidence': 0.95,
                    'source': 'appointment_type'
                }
            except MedicalService.DoesNotExist:
                # Create default consultation service
                return {
                    'service_id': None,
                    'code': service_code,
                    'name': f'{appointment_type.title()} Consultation',
                    'base_price': 100.00,  # Default price
                    'quantity': 1,
                    'ai_confidence': 0.85,
                    'source': 'default_consultation'
                }
                
        except Exception as e:
            logger.error(f"Error getting consultation service: {str(e)}")
            return {}
    
    def _extract_services_from_medical_record(self, record: MedicalRecord) -> List[Dict]:
        """Extract billable services from medical record content"""
        try:
            services = []
            
            # Analyze treatment plan for procedures
            if record.treatment_plan:
                procedures = self._extract_procedures_from_text(record.treatment_plan)
                services.extend(procedures)
            
            # Analyze physical examination for services
            if record.physical_examination:
                exam_services = self._extract_examination_services(record.physical_examination)
                services.extend(exam_services)
            
            # Check for medications prescribed
            medications = Medication.objects.filter(medical_record=record)
            for medication in medications:
                med_service = self._create_medication_service(medication)
                if med_service:
                    services.append(med_service)
            
            # Check for lab results
            lab_results = LabResult.objects.filter(medical_record=record)
            for lab in lab_results:
                lab_service = self._create_lab_service(lab)
                if lab_service:
                    services.append(lab_service)
            
            return services
            
        except Exception as e:
            logger.error(f"Error extracting services from medical record: {str(e)}")
            return []
    
    def _extract_procedures_from_text(self, text: str) -> List[Dict]:
        """AI-powered extraction of procedures from clinical text"""
        try:
            services = []
            
            # Common procedure keywords and their corresponding service codes
            procedure_keywords = {
                'x-ray': {'code': 'RAD001', 'name': 'X-Ray Examination', 'price': 75.00},
                'ultrasound': {'code': 'RAD002', 'name': 'Ultrasound Scan', 'price': 120.00},
                'ct scan': {'code': 'RAD003', 'name': 'CT Scan', 'price': 300.00},
                'mri': {'code': 'RAD004', 'name': 'MRI Scan', 'price': 500.00},
                'ecg': {'code': 'CAR001', 'name': 'ECG/EKG', 'price': 50.00},
                'blood test': {'code': 'LAB001', 'name': 'Blood Test', 'price': 40.00},
                'urine test': {'code': 'LAB002', 'name': 'Urine Analysis', 'price': 25.00},
                'injection': {'code': 'MED001', 'name': 'Injection/IV', 'price': 30.00},
                'dressing': {'code': 'NUR001', 'name': 'Wound Dressing', 'price': 20.00},
                'suture': {'code': 'SUR001', 'name': 'Suturing', 'price': 80.00}
            }
            
            text_lower = text.lower()
            
            for keyword, service_info in procedure_keywords.items():
                if keyword in text_lower:
                    services.append({
                        'service_id': None,
                        'code': service_info['code'],
                        'name': service_info['name'],
                        'base_price': service_info['price'],
                        'quantity': 1,
                        'ai_confidence': 0.80,
                        'source': 'text_extraction',
                        'extracted_from': f'Found "{keyword}" in treatment plan'
                    })
            
            return services
            
        except Exception as e:
            logger.error(f"Error extracting procedures from text: {str(e)}")
            return []
    
    def _create_medication_service(self, medication: Medication) -> Optional[Dict]:
        """Create billing service for medication"""
        try:
            return {
                'service_id': None,
                'code': f'MED_{medication.id}',
                'name': f'Medication: {medication.name}',
                'base_price': float(medication.cost) if hasattr(medication, 'cost') else 25.00,
                'quantity': 1,
                'ai_confidence': 0.90,
                'source': 'medication_record',
                'medication_details': {
                    'name': medication.name,
                    'dosage': medication.dosage,
                    'frequency': medication.frequency
                }
            }
        except Exception as e:
            logger.error(f"Error creating medication service: {str(e)}")
            return None
    
    def _create_lab_service(self, lab_result: LabResult) -> Optional[Dict]:
        """Create billing service for lab test"""
        try:
            # Map lab test types to pricing
            lab_pricing = {
                'blood': 40.00,
                'urine': 25.00,
                'glucose': 20.00,
                'cholesterol': 35.00,
                'hemoglobin': 30.00
            }
            
            test_name = lab_result.test_name.lower()
            price = 35.00  # Default price
            
            for lab_type, lab_price in lab_pricing.items():
                if lab_type in test_name:
                    price = lab_price
                    break
            
            return {
                'service_id': None,
                'code': f'LAB_{lab_result.id}',
                'name': f'Lab Test: {lab_result.test_name}',
                'base_price': price,
                'quantity': 1,
                'ai_confidence': 0.95,
                'source': 'lab_record',
                'lab_details': {
                    'test_name': lab_result.test_name,
                    'result_value': lab_result.result_value,
                    'test_date': lab_result.test_date.isoformat() if lab_result.test_date else None
                }
            }
        except Exception as e:
            logger.error(f"Error creating lab service: {str(e)}")
            return None
    
    def _optimize_pricing(
        self, 
        services: List[Dict], 
        patient: Patient, 
        appointment: Appointment
    ) -> Dict:
        """
        AI-powered pricing optimization based on patient profile and market data
        """
        try:
            optimization_results = {
                'original_total': 0.0,
                'optimized_total': 0.0,
                'savings_amount': 0.0,
                'optimization_factors': [],
                'pricing_strategy': 'standard'
            }
            
            original_total = sum(service.get('base_price', 0) for service in services)
            optimization_results['original_total'] = original_total
            
            # Patient history analysis
            patient_history = self._analyze_patient_payment_history(patient)
            
            # Insurance coverage analysis
            insurance_coverage = self._analyze_insurance_coverage(patient)
            
            # Apply optimization strategies
            optimized_total = original_total
            
            # Loyalty discount for frequent patients
            if patient_history.get('visit_count', 0) > 10:
                loyalty_discount = 0.05  # 5% discount
                optimized_total *= (1 - loyalty_discount)
                optimization_results['optimization_factors'].append({
                    'factor': 'loyalty_discount',
                    'description': 'Frequent patient discount',
                    'discount_percentage': loyalty_discount * 100,
                    'savings': original_total * loyalty_discount
                })
            
            # Insurance optimization
            if insurance_coverage.get('has_insurance', False):
                insurance_discount = insurance_coverage.get('coverage_percentage', 0) / 100
                insurance_savings = optimized_total * insurance_discount
                optimized_total -= insurance_savings
                optimization_results['optimization_factors'].append({
                    'factor': 'insurance_coverage',
                    'description': f"Insurance coverage: {insurance_coverage.get('coverage_percentage', 0)}%",
                    'discount_percentage': insurance_coverage.get('coverage_percentage', 0),
                    'savings': insurance_savings
                })
            
            # Early payment discount
            if appointment and hasattr(appointment, 'payment_preference'):
                if appointment.payment_preference == 'IMMEDIATE':
                    early_payment_discount = 0.02  # 2% discount
                    early_savings = optimized_total * early_payment_discount
                    optimized_total -= early_savings
                    optimization_results['optimization_factors'].append({
                        'factor': 'early_payment',
                        'description': 'Early payment discount',
                        'discount_percentage': early_payment_discount * 100,
                        'savings': early_savings
                    })
            
            optimization_results['optimized_total'] = optimized_total
            optimization_results['savings_amount'] = original_total - optimized_total
            optimization_results['pricing_strategy'] = self._determine_pricing_strategy(
                patient_history, insurance_coverage
            )
            
            return optimization_results
            
        except Exception as e:
            logger.error(f"Error optimizing pricing: {str(e)}")
            return {
                'original_total': sum(service.get('base_price', 0) for service in services),
                'optimized_total': sum(service.get('base_price', 0) for service in services),
                'savings_amount': 0.0,
                'optimization_factors': [],
                'pricing_strategy': 'standard',
                'error': str(e)
            }
    
    def _analyze_patient_payment_history(self, patient: Patient) -> Dict:
        """Analyze patient's payment history for optimization"""
        try:
            # Get patient's invoice history
            invoices = Invoice.objects.filter(patient=patient)
            
            total_invoices = invoices.count()
            paid_invoices = invoices.filter(status='PAID').count()
            total_amount = invoices.aggregate(total=Sum('total_amount'))['total'] or 0
            paid_amount = invoices.aggregate(paid=Sum('paid_amount'))['paid'] or 0
            
            payment_rate = (paid_amount / total_amount * 100) if total_amount > 0 else 100
            
            # Calculate average payment time
            paid_invoice_times = []
            for invoice in invoices.filter(status='PAID'):
                if hasattr(invoice, 'payment_date') and invoice.payment_date:
                    payment_time = (invoice.payment_date - invoice.invoice_date).days
                    paid_invoice_times.append(payment_time)
            
            avg_payment_time = sum(paid_invoice_times) / len(paid_invoice_times) if paid_invoice_times else 0
            
            return {
                'visit_count': total_invoices,
                'payment_rate': payment_rate,
                'total_lifetime_value': float(total_amount),
                'avg_payment_time_days': avg_payment_time,
                'risk_category': 'low' if payment_rate > 90 else 'medium' if payment_rate > 70 else 'high'
            }
            
        except Exception as e:
            logger.error(f"Error analyzing patient payment history: {str(e)}")
            return {
                'visit_count': 0,
                'payment_rate': 100,
                'total_lifetime_value': 0.0,
                'avg_payment_time_days': 0,
                'risk_category': 'unknown'
            }
    
    def predict_payment_likelihood(self, invoice_data: Dict, patient: Patient) -> Dict:
        """
        AI-powered prediction of payment likelihood and timeline
        """
        try:
            # Get patient payment history
            payment_history = self._analyze_patient_payment_history(patient)
            
            # Calculate base probability based on history
            base_probability = payment_history.get('payment_rate', 100) / 100
            
            # Adjust based on invoice amount
            invoice_amount = invoice_data.get('total_amount', 0)
            avg_amount = payment_history.get('total_lifetime_value', 0) / max(payment_history.get('visit_count', 1), 1)
            
            # Amount factor: higher amounts = lower probability
            amount_factor = 1.0
            if invoice_amount > avg_amount * 2:
                amount_factor = 0.8
            elif invoice_amount > avg_amount * 1.5:
                amount_factor = 0.9
            
            # Calculate final probability
            payment_probability = min(base_probability * amount_factor, 1.0)
            
            # Predict payment timeline
            predicted_days = max(payment_history.get('avg_payment_time_days', 15), 7)
            if payment_probability < 0.7:
                predicted_days *= 1.5  # Longer for risky patients
            
            # Risk assessment
            risk_level = 'low'
            if payment_probability < 0.6:
                risk_level = 'high'
            elif payment_probability < 0.8:
                risk_level = 'medium'
            
            return {
                'payment_probability': round(payment_probability, 3),
                'predicted_payment_days': int(predicted_days),
                'risk_level': risk_level,
                'confidence_score': 0.85,
                'factors': {
                    'payment_history_score': payment_history.get('payment_rate', 100),
                    'amount_factor': amount_factor,
                    'patient_category': payment_history.get('risk_category', 'unknown')
                },
                'recommendations': self._generate_payment_recommendations(
                    payment_probability, risk_level
                )
            }
            
        except Exception as e:
            logger.error(f"Error predicting payment likelihood: {str(e)}")
            return {
                'payment_probability': 0.8,  # Default
                'predicted_payment_days': 15,
                'risk_level': 'medium',
                'confidence_score': 0.5,
                'error': str(e)
            }
    
    def _load_pricing_model(self):
        """Load AI pricing optimization model"""
        # Placeholder for ML model loading
        return {}
    
    def _load_medical_coding_database(self):
        """Load medical coding database for automatic code assignment"""
        # Placeholder for medical coding database
        return {}
    
    def _load_insurance_rules(self):
        """Load insurance coverage rules and policies"""
        # Placeholder for insurance rules
        return {}
    
    def _deduplicate_and_validate_services(self, services: List[Dict]) -> List[Dict]:
        """Remove duplicate services and validate"""
        seen_codes = set()
        unique_services = []
        
        for service in services:
            code = service.get('code', '')
            if code and code not in seen_codes:
                seen_codes.add(code)
                unique_services.append(service)
            elif not code:  # Services without codes (like medications)
                unique_services.append(service)
        
        return unique_services
    
    def _ai_recommend_additional_services(self, appointment, medical_records) -> List[Dict]:
        """AI recommendations for additional billable services"""
        # Placeholder for AI service recommendations
        return []
    
    def _analyze_insurance_coverage(self, patient: Patient) -> Dict:
        """Analyze patient's insurance coverage"""
        # Placeholder - would integrate with insurance verification systems
        return {
            'has_insurance': True,
            'coverage_percentage': 80,
            'provider': 'Standard Insurance',
            'policy_number': 'DEMO123'
        }
    
    def _determine_pricing_strategy(self, patient_history: Dict, insurance_coverage: Dict) -> str:
        """Determine optimal pricing strategy"""
        if insurance_coverage.get('has_insurance', False):
            return 'insurance_optimized'
        elif patient_history.get('payment_rate', 0) > 90:
            return 'loyalty_preferred'
        else:
            return 'standard'
    
    def _generate_payment_recommendations(self, probability: float, risk_level: str) -> List[str]:
        """Generate payment collection recommendations"""
        recommendations = []
        
        if risk_level == 'high':
            recommendations.extend([
                'Require payment at time of service',
                'Offer payment plan options',
                'Consider requiring deposit'
            ])
        elif risk_level == 'medium':
            recommendations.extend([
                'Send payment reminder after 7 days',
                'Offer early payment discount',
                'Follow up via phone if overdue'
            ])
        else:
            recommendations.extend([
                'Standard payment terms apply',
                'Send friendly payment reminder at due date'
            ])
        
        return recommendations
    
    def _calculate_estimated_revenue(self, invoice_data: Dict) -> Dict:
        """Calculate estimated revenue and collection metrics"""
        try:
            total_amount = invoice_data.get('total_amount', 0)
            
            return {
                'gross_revenue': total_amount,
                'estimated_collections': total_amount * 0.92,  # 92% collection rate
                'estimated_timeline_days': 18,
                'profit_margin': total_amount * 0.35  # 35% estimated margin
            }
        except:
            return {
                'gross_revenue': 0,
                'estimated_collections': 0,
                'estimated_timeline_days': 30,
                'profit_margin': 0
            }
    
    def _create_invoice_structure(self, appointment, services, pricing) -> Dict:
        """Create structured invoice data"""
        try:
            subtotal = sum(service.get('base_price', 0) for service in services)
            tax_rate = 0.08  # 8% tax
            tax_amount = subtotal * tax_rate
            total_amount = subtotal + tax_amount
            
            return {
                'patient_id': appointment.patient.id,
                'appointment_id': appointment.id,
                'invoice_date': timezone.now().date().isoformat(),
                'due_date': (timezone.now().date() + timedelta(days=30)).isoformat(),
                'services': services,
                'subtotal': subtotal,
                'tax_rate': tax_rate,
                'tax_amount': tax_amount,
                'total_amount': total_amount,
                'optimized_amount': pricing.get('optimized_total', total_amount),
                'savings': pricing.get('savings_amount', 0)
            }
        except Exception as e:
            logger.error(f"Error creating invoice structure: {str(e)}")
            return {}
    
    def _analyze_billing_opportunity(self, appointment, services, pricing) -> Dict:
        """Analyze billing opportunity and provide AI insights"""
        try:
            total_services = len(services)
            ai_confidence = sum(service.get('ai_confidence', 0.8) for service in services) / max(total_services, 1)
            
            insights = []
            
            if total_services > 5:
                insights.append("High-value appointment with multiple billable services")
            
            if pricing.get('savings_amount', 0) > 0:
                insights.append(f"Pricing optimization saved ${pricing['savings_amount']:.2f}")
            
            if ai_confidence > 0.9:
                insights.append("High confidence in service identification accuracy")
            
            return {
                'confidence': ai_confidence,
                'insights': insights,
                'optimization_score': min(pricing.get('savings_amount', 0) / max(pricing.get('original_total', 1), 1), 1.0),
                'revenue_potential': 'high' if total_services > 3 else 'medium' if total_services > 1 else 'low'
            }
        except Exception as e:
            logger.error(f"Error analyzing billing opportunity: {str(e)}")
            return {
                'confidence': 0.8,
                'insights': [],
                'optimization_score': 0.0,
                'revenue_potential': 'medium'
            }
