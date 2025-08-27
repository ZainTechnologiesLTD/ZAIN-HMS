# apps/emr/ai_clinical_engine.py
"""
AI-Powered Clinical Decision Support Engine
Provides intelligent clinical recommendations, drug interaction analysis, and diagnostic assistance
"""

import datetime
import json
import logging
from typing import Dict, List, Optional, Tuple
from django.db.models import Q
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


class ClinicalDecisionEngine:
    """
    AI-powered clinical decision support system
    """
    
    def __init__(self, hospital_id: str = None):
        self.hospital_id = hospital_id or self._get_default_hospital_id()
        self.cache_timeout = 600  # 10 minutes
        
        # Clinical knowledge base (would be loaded from external sources in production)
        self.drug_interactions = self._load_drug_interactions()
        self.symptom_disease_mapping = self._load_symptom_disease_mapping()
        self.vital_ranges = self._load_vital_ranges()
        self.lab_ranges = self._load_lab_ranges()
    
    def _get_default_hospital_id(self):
        """Get a default hospital ID for testing purposes"""
        try:
            # Try to import and get first hospital
            from django.apps import apps
            Hospital = apps.get_model('hospitals', 'Hospital')
            hospital = Hospital.objects.first()
            return hospital.hospital_id if hospital else 'DEMO001'
        except:
            return 'DEMO001'
    
    def analyze_patient_symptoms(
        self, 
        symptoms: List[str], 
        patient_age: int, 
        patient_gender: str,
        medical_history: List[str] = None
    ) -> Dict:
        """
        Analyze patient symptoms and provide diagnostic suggestions
        
        Args:
            symptoms: List of patient symptoms
            patient_age: Patient age
            patient_gender: Patient gender
            medical_history: Previous medical conditions
            
        Returns:
            Dictionary with diagnostic suggestions and recommendations
        """
        try:
            cache_key = f"symptom_analysis_{hash(tuple(symptoms))}_{patient_age}_{patient_gender}"
            cached_result = cache.get(cache_key)
            
            if cached_result:
                logger.info(f"Retrieved cached symptom analysis for patient")
                return cached_result
            
            # Analyze symptoms using AI logic
            diagnostic_suggestions = self._generate_diagnostic_suggestions(
                symptoms, patient_age, patient_gender, medical_history or []
            )
            
            # Calculate confidence scores
            confidence_scores = self._calculate_diagnostic_confidence(
                symptoms, diagnostic_suggestions
            )
            
            # Generate clinical recommendations
            recommendations = self._generate_clinical_recommendations(
                diagnostic_suggestions, patient_age, patient_gender
            )
            
            # Flag urgent conditions
            urgent_flags = self._identify_urgent_conditions(symptoms, diagnostic_suggestions)
            
            result = {
                'diagnostic_suggestions': diagnostic_suggestions,
                'confidence_scores': confidence_scores,
                'clinical_recommendations': recommendations,
                'urgent_flags': urgent_flags,
                'next_steps': self._generate_next_steps(diagnostic_suggestions),
                'analysis_timestamp': timezone.now().isoformat()
            }
            
            # Cache the result
            cache.set(cache_key, result, self.cache_timeout)
            
            logger.info(f"Generated diagnostic analysis with {len(diagnostic_suggestions)} suggestions")
            return result
            
        except Exception as e:
            logger.error(f"Error in symptom analysis: {str(e)}")
            return {
                'diagnostic_suggestions': [],
                'confidence_scores': {},
                'clinical_recommendations': [],
                'urgent_flags': [],
                'next_steps': ['Consult with primary physician'],
                'error': 'Analysis unavailable'
            }
    
    def analyze_symptoms(self, symptoms: List[str], patient_age: int, patient_gender: str) -> Dict:
        """
        Simplified symptom analysis method for testing and basic use
        
        Args:
            symptoms: List of symptom strings
            patient_age: Patient age
            patient_gender: Patient gender ('M' or 'F')
            
        Returns:
            Dictionary with conditions and confidence scores
        """
        try:
            # Generate potential conditions based on symptoms
            conditions = []
            
            # Simple symptom-to-condition mapping for demonstration
            symptom_mappings = {
                'fever': [('common_cold', 0.6), ('flu', 0.7), ('pneumonia', 0.4)],
                'cough': [('common_cold', 0.7), ('bronchitis', 0.6), ('pneumonia', 0.5)],
                'shortness_of_breath': [('asthma', 0.6), ('pneumonia', 0.7), ('heart_failure', 0.4)],
                'chest_pain': [('heart_attack', 0.5), ('angina', 0.6), ('pneumonia', 0.3)],
                'headache': [('tension_headache', 0.7), ('migraine', 0.6), ('sinusitis', 0.4)],
                'nausea': [('gastroenteritis', 0.6), ('food_poisoning', 0.5), ('pregnancy', 0.3)],
                'fatigue': [('anemia', 0.5), ('depression', 0.4), ('thyroid_disorder', 0.4)],
                'weight_loss': [('hyperthyroidism', 0.5), ('diabetes', 0.4), ('cancer', 0.3)]
            }
            
            # Aggregate condition probabilities
            condition_scores = {}
            for symptom in symptoms:
                if symptom in symptom_mappings:
                    for condition, base_score in symptom_mappings[symptom]:
                        if condition not in condition_scores:
                            condition_scores[condition] = 0
                        condition_scores[condition] += base_score
            
            # Adjust for age and gender
            for condition in condition_scores:
                # Age adjustments
                if patient_age > 65:
                    if condition in ['heart_attack', 'heart_failure', 'pneumonia']:
                        condition_scores[condition] *= 1.2
                elif patient_age < 18:
                    if condition in ['common_cold', 'flu']:
                        condition_scores[condition] *= 1.1
                
                # Gender adjustments
                if patient_gender == 'F' and condition == 'heart_attack':
                    condition_scores[condition] *= 0.8
                elif patient_gender == 'M' and condition == 'migraine':
                    condition_scores[condition] *= 0.7
            
            # Normalize scores to probabilities
            max_score = max(condition_scores.values()) if condition_scores else 1
            for condition in condition_scores:
                condition_scores[condition] = min(condition_scores[condition] / max_score, 1.0)
            
            # Sort by probability
            sorted_conditions = sorted(
                condition_scores.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            
            # Format results
            conditions = [
                {
                    'condition': condition,
                    'probability': probability,
                    'confidence': 'high' if probability > 0.7 else 'medium' if probability > 0.4 else 'low'
                }
                for condition, probability in sorted_conditions[:5]  # Top 5
            ]
            
            overall_confidence = max(condition_scores.values()) if condition_scores else 0.3
            
            return {
                'conditions': conditions,
                'confidence': overall_confidence,
                'symptoms_analyzed': symptoms,
                'patient_demographics': {
                    'age': patient_age,
                    'gender': patient_gender
                }
            }
            
        except Exception as e:
            logger.error(f"Error in simplified symptom analysis: {str(e)}")
            return {
                'conditions': [{'condition': 'unknown', 'probability': 0.3, 'confidence': 'low'}],
                'confidence': 0.3,
                'symptoms_analyzed': symptoms,
                'error': str(e)
            }
    
    def check_drug_interactions(
        self, 
        medications, 
        patient_conditions: List[str] = None
    ) -> List[Dict]:
        """
        Check for drug interactions and contraindications
        
        Args:
            medications: List of medication names (strings) or medication dictionaries
            patient_conditions: Patient's current medical conditions
            
        Returns:
            List of drug interactions
        """
        try:
            interactions = []
            
            # Convert string list to medication objects if needed
            if medications and isinstance(medications[0], str):
                med_objects = [{'name': med, 'dosage': '', 'frequency': ''} for med in medications]
            else:
                med_objects = medications
            
            # Known drug interactions database (simplified for demonstration)
            interaction_db = {
                ('warfarin', 'aspirin'): {
                    'severity': 'MAJOR',
                    'description': 'Increased risk of bleeding when warfarin is combined with aspirin',
                    'recommendation': 'Monitor INR closely and consider alternative antiplatelet therapy'
                },
                ('metformin', 'insulin'): {
                    'severity': 'MODERATE',
                    'description': 'Combined use may increase risk of hypoglycemia',
                    'recommendation': 'Monitor blood glucose levels closely'
                },
                ('lisinopril', 'hydrochlorothiazide'): {
                    'severity': 'MINOR',
                    'description': 'May cause additive hypotensive effects',
                    'recommendation': 'Monitor blood pressure regularly'
                },
                ('simvastatin', 'amlodipine'): {
                    'severity': 'MODERATE',
                    'description': 'Amlodipine may increase simvastatin levels',
                    'recommendation': 'Consider reducing simvastatin dose'
                }
            }
            
            # Check drug-drug interactions
            for i, med1 in enumerate(med_objects):
                med1_name = med1['name'].lower() if isinstance(med1, dict) else med1.lower()
                for med2 in med_objects[i+1:]:
                    med2_name = med2['name'].lower() if isinstance(med2, dict) else med2.lower()
                    
                    # Check both directions
                    interaction_key1 = (med1_name, med2_name)
                    interaction_key2 = (med2_name, med1_name)
                    
                    if interaction_key1 in interaction_db:
                        interaction = interaction_db[interaction_key1].copy()
                        interaction['drug1'] = med1_name
                        interaction['drug2'] = med2_name
                        interactions.append(interaction)
                    elif interaction_key2 in interaction_db:
                        interaction = interaction_db[interaction_key2].copy()
                        interaction['drug1'] = med2_name
                        interaction['drug2'] = med1_name
                        interactions.append(interaction)
            
            return interactions
            
        except Exception as e:
            logger.error(f"Error checking drug interactions: {str(e)}")
            return []
    
    def analyze_vital_signs(
        self, 
        vital_signs: Dict = None, 
        patient_age: int = None, 
        patient_gender: str = None,
        medical_history: List[str] = None,
        blood_pressure_systolic: int = None,
        blood_pressure_diastolic: int = None,
        heart_rate: int = None,
        temperature: float = None,
        respiratory_rate: int = None,
        oxygen_saturation: int = None,
        **kwargs
    ) -> Dict:
        """
        Analyze vital signs and provide clinical insights
        
        Args:
            vital_signs: Dictionary with vital sign measurements (optional if individual params provided)
            patient_age: Patient age
            patient_gender: Patient gender
            medical_history: Patient's medical history
            blood_pressure_systolic: Systolic BP
            blood_pressure_diastolic: Diastolic BP
            heart_rate: Heart rate in BPM
            temperature: Temperature in Celsius
            respiratory_rate: Respiratory rate
            oxygen_saturation: Oxygen saturation percentage
            
        Returns:
            Vital signs analysis with alerts and recommendations
        """
        try:
            # If individual parameters are provided, create vital_signs dict
            if vital_signs is None:
                vital_signs = {}
                if blood_pressure_systolic is not None:
                    vital_signs['blood_pressure_systolic'] = blood_pressure_systolic
                if blood_pressure_diastolic is not None:
                    vital_signs['blood_pressure_diastolic'] = blood_pressure_diastolic
                if heart_rate is not None:
                    vital_signs['heart_rate'] = heart_rate
                if temperature is not None:
                    vital_signs['temperature'] = temperature
                if respiratory_rate is not None:
                    vital_signs['respiratory_rate'] = respiratory_rate
                if oxygen_saturation is not None:
                    vital_signs['oxygen_saturation'] = oxygen_saturation
            
            analysis_results = {}
            alerts = []
            recommendations = []
            
            # Define normal ranges for demonstration
            normal_ranges = {
                'blood_pressure_systolic': (90, 140),
                'blood_pressure_diastolic': (60, 90),
                'heart_rate': (60, 100),
                'temperature': (36.1, 37.5),
                'respiratory_rate': (12, 20),
                'oxygen_saturation': (95, 100)
            }
            
            # Analyze each vital sign
            risk_level = 'low'
            for vital_name, value in vital_signs.items():
                if vital_name in normal_ranges:
                    min_val, max_val = normal_ranges[vital_name]
                    
                    if value < min_val:
                        status = 'LOW'
                        severity = 'HIGH' if value < min_val * 0.8 else 'MODERATE'
                    elif value > max_val:
                        status = 'HIGH'
                        severity = 'HIGH' if value > max_val * 1.2 else 'MODERATE'
                    else:
                        status = 'NORMAL'
                        severity = 'NONE'
                    
                    analysis_results[vital_name] = {
                        'value': value,
                        'status': status,
                        'severity': severity,
                        'normal_range': f"{min_val}-{max_val}"
                    }
                    
                    if status != 'NORMAL':
                        alerts.append({
                            'vital': vital_name,
                            'value': value,
                            'status': status,
                            'severity': severity,
                            'message': f"{vital_name.replace('_', ' ').title()} is {status.lower()}: {value}"
                        })
                        
                        if severity == 'HIGH':
                            risk_level = 'high'
                        elif severity == 'MODERATE' and risk_level != 'high':
                            risk_level = 'moderate'
            
            # Generate overall assessment
            if len(alerts) > 2:
                risk_level = 'high'
            elif len(alerts) > 0 and risk_level == 'low':
                risk_level = 'moderate'
            
            return {
                'analysis_results': analysis_results,
                'alerts': alerts,
                'risk_level': risk_level,
                'total_alerts': len(alerts),
                'recommendations': [
                    'Monitor patient closely',
                    'Consider immediate intervention if high-risk vitals persist',
                    'Document all vital sign abnormalities'
                ] if alerts else ['Vitals within normal limits'],
                'analysis_timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing vital signs: {str(e)}")
            return {
                'analysis_results': {},
                'alerts': [],
                'risk_level': 'unknown',
                'error': str(e)
            }
    
    def interpret_lab_results(self, lab_results: Dict) -> Dict:
        """
        Interpret laboratory results with AI analysis
        
        Args:
            lab_results: Dictionary of lab test names and values
            
        Returns:
            Dictionary with interpretations and clinical significance
        """
        try:
            interpretations = []
            
            # Normal ranges for common lab tests
            normal_ranges = {
                'hemoglobin': {'male': (13.8, 17.2), 'female': (12.1, 15.1), 'unit': 'g/dL'},
                'white_blood_cells': {'all': (4500, 11000), 'unit': 'cells/μL'},
                'glucose': {'fasting': (70, 100), 'random': (70, 140), 'unit': 'mg/dL'},
                'cholesterol': {'all': (0, 200), 'unit': 'mg/dL'},
                'creatinine': {'male': (0.7, 1.3), 'female': (0.6, 1.1), 'unit': 'mg/dL'}
            }
            
            for test_name, value in lab_results.items():
                if test_name in normal_ranges:
                    test_info = normal_ranges[test_name]
                    
                    # Determine normal range (simplified - assumes general range)
                    if 'all' in test_info:
                        min_val, max_val = test_info['all']
                    elif 'male' in test_info:  # Default to male range for simplicity
                        min_val, max_val = test_info['male']
                    else:
                        min_val, max_val = test_info['fasting']  # Default for glucose
                    
                    # Determine status
                    if value < min_val:
                        status = 'LOW'
                        significance = 'Monitor for underlying conditions'
                    elif value > max_val:
                        status = 'HIGH'
                        significance = 'May indicate disease or require intervention'
                    else:
                        status = 'NORMAL'
                        significance = 'Within normal limits'
                    
                    interpretation = {
                        'test': test_name,
                        'value': value,
                        'unit': test_info['unit'],
                        'normal_range': f"{min_val}-{max_val}",
                        'status': status,
                        'clinical_significance': significance
                    }
                    
                    # Add specific interpretations
                    if test_name == 'hemoglobin' and status == 'LOW':
                        interpretation['clinical_significance'] = 'Possible anemia - investigate further'
                    elif test_name == 'white_blood_cells' and status == 'HIGH':
                        interpretation['clinical_significance'] = 'Possible infection or inflammatory condition'
                    elif test_name == 'glucose' and status == 'HIGH':
                        interpretation['clinical_significance'] = 'Possible diabetes or pre-diabetes - confirm with additional testing'
                    
                    interpretations.append(interpretation)
            
            return {
                'interpretations': interpretations,
                'overall_assessment': 'Review all abnormal values with clinical context',
                'analysis_timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error interpreting lab results: {str(e)}")
            return {
                'interpretations': [],
                'error': str(e)
            }
    
    def analyze_lab_results(
        self, 
        lab_results: Dict, 
        patient_age: int, 
        patient_gender: str,
        medical_history: List[str] = None
    ) -> Dict:
        """
        Analyze laboratory results and provide clinical insights
        
        Args:
            lab_results: Dictionary with lab test results
            patient_age: Patient age
            patient_gender: Patient gender
            medical_history: Patient's medical history
            
        Returns:
            Lab analysis with clinical interpretations
        """
        try:
            analysis_results = {}
            abnormal_results = []
            clinical_insights = []
            
            for test_name, value in lab_results.items():
                if test_name in self.lab_ranges:
                    analysis = self._analyze_single_lab_result(
                        test_name, value, patient_age, patient_gender
                    )
                    analysis_results[test_name] = analysis
                    
                    if analysis['status'] != 'NORMAL':
                        abnormal_results.append({
                            'test': test_name,
                            'value': value,
                            'reference_range': analysis['reference_range'],
                            'status': analysis['status'],
                            'severity': analysis['severity'],
                            'clinical_significance': analysis['clinical_significance']
                        })
            
            # Generate pattern-based insights
            pattern_insights = self._identify_lab_patterns(analysis_results, medical_history)
            clinical_insights.extend(pattern_insights)
            
            # Check for disease markers
            disease_markers = self._check_disease_markers(analysis_results)
            clinical_insights.extend(disease_markers)
            
            # Generate follow-up recommendations
            follow_up_recommendations = self._generate_lab_follow_up_recommendations(
                abnormal_results, pattern_insights
            )
            
            return {
                'lab_analysis': analysis_results,
                'abnormal_results': abnormal_results,
                'clinical_insights': clinical_insights,
                'follow_up_recommendations': follow_up_recommendations,
                'overall_assessment': self._generate_overall_lab_assessment(
                    abnormal_results, clinical_insights
                ),
                'analysis_timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in lab results analysis: {str(e)}")
            return {
                'lab_analysis': {},
                'abnormal_results': [],
                'clinical_insights': [],
                'follow_up_recommendations': [],
                'overall_assessment': 'Analysis unavailable',
                'error': 'Lab results analysis unavailable'
            }
    
    def generate_treatment_plan(
        self, 
        diagnosis: str, 
        patient_data: Dict,
        severity: str = 'MODERATE'
    ) -> Dict:
        """
        Generate AI-assisted treatment plan based on diagnosis and patient data
        
        Args:
            diagnosis: Primary diagnosis
            patient_data: Patient information including age, gender, history
            severity: Condition severity level
            
        Returns:
            Comprehensive treatment plan with recommendations
        """
        try:
            # Generate medication recommendations
            medication_plan = self._generate_medication_plan(
                diagnosis, patient_data, severity
            )
            
            # Generate lifestyle recommendations
            lifestyle_recommendations = self._generate_lifestyle_recommendations(
                diagnosis, patient_data
            )
            
            # Generate monitoring plan
            monitoring_plan = self._generate_monitoring_plan(
                diagnosis, severity, patient_data
            )
            
            # Generate follow-up schedule
            follow_up_schedule = self._generate_follow_up_schedule(
                diagnosis, severity
            )
            
            # Calculate treatment duration
            treatment_duration = self._estimate_treatment_duration(
                diagnosis, severity, patient_data
            )
            
            return {
                'diagnosis': diagnosis,
                'severity': severity,
                'medication_plan': medication_plan,
                'lifestyle_recommendations': lifestyle_recommendations,
                'monitoring_plan': monitoring_plan,
                'follow_up_schedule': follow_up_schedule,
                'estimated_duration': treatment_duration,
                'success_probability': self._calculate_treatment_success_probability(
                    diagnosis, patient_data, severity
                ),
                'alternative_treatments': self._suggest_alternative_treatments(
                    diagnosis, patient_data
                ),
                'created_timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating treatment plan: {str(e)}")
            return {
                'diagnosis': diagnosis,
                'severity': severity,
                'medication_plan': [],
                'lifestyle_recommendations': [],
                'monitoring_plan': [],
                'follow_up_schedule': [],
                'estimated_duration': 'Unknown',
                'success_probability': 0.5,
                'alternative_treatments': [],
                'error': 'Treatment plan generation unavailable'
            }
    
    # Private helper methods
    
    def _load_drug_interactions(self) -> Dict:
        """Load drug interaction database"""
        return {
            'warfarin': {
                'interactions': ['aspirin', 'ibuprofen', 'alcohol'],
                'severity': 'HIGH',
                'mechanism': 'Increased bleeding risk'
            },
            'metformin': {
                'interactions': ['contrast_dye', 'alcohol'],
                'severity': 'MEDIUM',
                'mechanism': 'Lactic acidosis risk'
            }
            # In production, this would be loaded from a comprehensive database
        }
    
    def _load_symptom_disease_mapping(self) -> Dict:
        """Load symptom to disease mapping"""
        return {
            'chest_pain': {
                'possible_conditions': [
                    {'condition': 'Myocardial Infarction', 'probability': 0.3, 'urgency': 'CRITICAL'},
                    {'condition': 'Angina', 'probability': 0.25, 'urgency': 'HIGH'},
                    {'condition': 'Gastroesophageal Reflux', 'probability': 0.2, 'urgency': 'LOW'},
                    {'condition': 'Muscle Strain', 'probability': 0.15, 'urgency': 'LOW'}
                ]
            },
            'fever': {
                'possible_conditions': [
                    {'condition': 'Viral Infection', 'probability': 0.4, 'urgency': 'LOW'},
                    {'condition': 'Bacterial Infection', 'probability': 0.3, 'urgency': 'MEDIUM'},
                    {'condition': 'Pneumonia', 'probability': 0.2, 'urgency': 'HIGH'},
                    {'condition': 'Sepsis', 'probability': 0.1, 'urgency': 'CRITICAL'}
                ]
            }
            # Comprehensive mapping would be loaded from medical knowledge base
        }
    
    def _load_vital_ranges(self) -> Dict:
        """Load normal vital sign ranges by age and gender"""
        return {
            'blood_pressure_systolic': {
                'adult': {'min': 90, 'max': 140, 'optimal': 120},
                'elderly': {'min': 90, 'max': 150, 'optimal': 130}
            },
            'blood_pressure_diastolic': {
                'adult': {'min': 60, 'max': 90, 'optimal': 80},
                'elderly': {'min': 60, 'max': 95, 'optimal': 85}
            },
            'heart_rate': {
                'adult': {'min': 60, 'max': 100, 'optimal': 70},
                'athlete': {'min': 40, 'max': 60, 'optimal': 50}
            },
            'temperature': {
                'normal': {'min': 36.1, 'max': 37.2, 'optimal': 36.6}
            },
            'oxygen_saturation': {
                'normal': {'min': 95, 'max': 100, 'optimal': 98}
            }
        }
    
    def _load_lab_ranges(self) -> Dict:
        """Load normal laboratory value ranges"""
        return {
            'glucose': {
                'fasting': {'min': 70, 'max': 100, 'unit': 'mg/dL'},
                'random': {'min': 70, 'max': 140, 'unit': 'mg/dL'}
            },
            'cholesterol_total': {
                'normal': {'min': 0, 'max': 200, 'unit': 'mg/dL'},
                'borderline': {'min': 200, 'max': 239, 'unit': 'mg/dL'}
            },
            'hemoglobin': {
                'male': {'min': 13.8, 'max': 17.2, 'unit': 'g/dL'},
                'female': {'min': 12.1, 'max': 15.1, 'unit': 'g/dL'}
            }
        }
    
    def _generate_diagnostic_suggestions(
        self, 
        symptoms: List[str], 
        age: int, 
        gender: str, 
        history: List[str]
    ) -> List[Dict]:
        """Generate diagnostic suggestions based on symptoms"""
        suggestions = []
        
        for symptom in symptoms:
            if symptom in self.symptom_disease_mapping:
                conditions = self.symptom_disease_mapping[symptom]['possible_conditions']
                for condition in conditions:
                    # Adjust probability based on age, gender, and history
                    adjusted_probability = self._adjust_probability_for_demographics(
                        condition['probability'], age, gender, history, condition['condition']
                    )
                    
                    suggestions.append({
                        'condition': condition['condition'],
                        'probability': adjusted_probability,
                        'urgency': condition['urgency'],
                        'supporting_symptom': symptom
                    })
        
        # Remove duplicates and sort by probability
        unique_suggestions = {}
        for suggestion in suggestions:
            condition = suggestion['condition']
            if condition not in unique_suggestions or suggestion['probability'] > unique_suggestions[condition]['probability']:
                unique_suggestions[condition] = suggestion
        
        return sorted(unique_suggestions.values(), key=lambda x: x['probability'], reverse=True)
    
    def _calculate_diagnostic_confidence(
        self, 
        symptoms: List[str], 
        suggestions: List[Dict]
    ) -> Dict:
        """Calculate confidence scores for diagnostic suggestions"""
        confidence_scores = {}
        
        for suggestion in suggestions:
            base_confidence = suggestion['probability']
            
            # Adjust confidence based on symptom specificity
            symptom_specificity = self._calculate_symptom_specificity(
                symptoms, suggestion['condition']
            )
            
            # Adjust confidence based on symptom count
            symptom_count_factor = min(len(symptoms) / 3.0, 1.0)  # Max factor at 3+ symptoms
            
            final_confidence = base_confidence * symptom_specificity * symptom_count_factor
            confidence_scores[suggestion['condition']] = min(final_confidence, 0.95)
        
        return confidence_scores
    
    def _generate_clinical_recommendations(
        self, 
        suggestions: List[Dict], 
        age: int, 
        gender: str
    ) -> List[str]:
        """Generate clinical recommendations based on diagnostic suggestions"""
        recommendations = []
        
        # Check for high-urgency conditions
        high_urgency = [s for s in suggestions if s['urgency'] in ['CRITICAL', 'HIGH']]
        if high_urgency:
            recommendations.append('Immediate medical evaluation recommended')
            recommendations.append('Consider emergency department visit if symptoms worsen')
        
        # Age-specific recommendations
        if age > 65:
            recommendations.append('Monitor for complications due to advanced age')
            recommendations.append('Consider medication interactions with existing prescriptions')
        
        # Gender-specific recommendations
        if gender == 'F' and age >= 18 and age <= 50:
            recommendations.append('Consider pregnancy-related conditions if applicable')
        
        return recommendations
    
    def _identify_urgent_conditions(
        self, 
        symptoms: List[str], 
        suggestions: List[Dict]
    ) -> List[Dict]:
        """Identify urgent conditions requiring immediate attention"""
        urgent_flags = []
        
        critical_symptoms = ['chest_pain', 'difficulty_breathing', 'severe_headache', 'loss_of_consciousness']
        urgent_symptoms = [s for s in symptoms if s in critical_symptoms]
        
        for symptom in urgent_symptoms:
            urgent_flags.append({
                'symptom': symptom,
                'urgency_level': 'CRITICAL',
                'action_required': 'Immediate medical evaluation',
                'time_frame': 'Within 30 minutes'
            })
        
        # Check for high-probability critical conditions
        critical_conditions = [s for s in suggestions if s['urgency'] == 'CRITICAL' and s['probability'] > 0.3]
        for condition in critical_conditions:
            urgent_flags.append({
                'condition': condition['condition'],
                'urgency_level': 'CRITICAL',
                'probability': condition['probability'],
                'action_required': 'Emergency department evaluation',
                'time_frame': 'Immediately'
            })
        
        return urgent_flags
    
    def _generate_next_steps(self, suggestions: List[Dict]) -> List[str]:
        """Generate next steps based on diagnostic suggestions"""
        next_steps = []
        
        if not suggestions:
            return ['Schedule appointment with primary care physician']
        
        top_suggestion = suggestions[0]
        
        if top_suggestion['urgency'] == 'CRITICAL':
            next_steps.append('Seek immediate emergency medical care')
        elif top_suggestion['urgency'] == 'HIGH':
            next_steps.append('Schedule urgent appointment with physician')
            next_steps.append('Monitor symptoms closely')
        else:
            next_steps.append('Schedule routine appointment with primary care physician')
            next_steps.append('Continue monitoring symptoms')
        
        # Add diagnostic test recommendations
        if top_suggestion['probability'] > 0.5:
            next_steps.append(f"Consider diagnostic tests for {top_suggestion['condition']}")
        
        return next_steps
    
    def _check_drug_drug_interaction(self, med1: Dict, med2: Dict) -> Optional[Dict]:
        """Check for interaction between two medications"""
        drug1_name = med1.get('name', '').lower()
        drug2_name = med2.get('name', '').lower()
        
        # Check in both directions
        for drug1, drug2 in [(drug1_name, drug2_name), (drug2_name, drug1_name)]:
            if drug1 in self.drug_interactions:
                if drug2 in self.drug_interactions[drug1]['interactions']:
                    return {
                        'drug1': med1['name'],
                        'drug2': med2['name'],
                        'severity': self.drug_interactions[drug1]['severity'],
                        'mechanism': self.drug_interactions[drug1]['mechanism'],
                        'recommendation': 'Consult physician before combining these medications'
                    }
        
        return None
    
    def _check_drug_condition_interaction(self, medication: Dict, condition: str) -> Optional[Dict]:
        """Check for drug-condition contraindications"""
        # This would check against a comprehensive database
        contraindications = {
            'warfarin': ['bleeding_disorders', 'liver_disease'],
            'metformin': ['kidney_disease', 'liver_disease'],
            'aspirin': ['bleeding_disorders', 'peptic_ulcer']
        }
        
        drug_name = medication.get('name', '').lower()
        condition_lower = condition.lower()
        
        if drug_name in contraindications:
            if any(contraindication in condition_lower for contraindication in contraindications[drug_name]):
                return {
                    'medication': medication['name'],
                    'condition': condition,
                    'severity': 'HIGH',
                    'recommendation': 'Avoid this medication due to medical condition'
                }
        
        return None
    
    def _check_dosage_appropriateness(self, medication: Dict) -> Optional[Dict]:
        """Check if medication dosage is appropriate"""
        # This would check against dosage guidelines
        # For now, just basic validation
        
        if 'dosage' not in medication:
            return {
                'medication': medication['name'],
                'issue': 'Missing dosage information',
                'severity': 'MEDIUM',
                'recommendation': 'Specify exact dosage and frequency'
            }
        
        return None
    
    def _calculate_medication_risk_score(
        self, 
        interactions: List[Dict], 
        contraindications: List[Dict], 
        warnings: List[Dict]
    ) -> float:
        """Calculate overall medication risk score"""
        risk_score = 0.0
        
        # Add risk for interactions
        for interaction in interactions:
            if interaction['severity'] == 'HIGH':
                risk_score += 0.4
            elif interaction['severity'] == 'MEDIUM':
                risk_score += 0.2
            else:
                risk_score += 0.1
        
        # Add risk for contraindications
        for contraindication in contraindications:
            if contraindication['severity'] == 'HIGH':
                risk_score += 0.5
            else:
                risk_score += 0.3
        
        # Add risk for warnings
        risk_score += len(warnings) * 0.1
        
        return min(risk_score, 1.0)
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to risk level"""
        if risk_score >= 0.7:
            return 'HIGH'
        elif risk_score >= 0.4:
            return 'MEDIUM'
        elif risk_score >= 0.1:
            return 'LOW'
        else:
            return 'MINIMAL'
    
    def _generate_medication_recommendations(
        self, 
        interactions: List[Dict], 
        contraindications: List[Dict], 
        warnings: List[Dict]
    ) -> List[str]:
        """Generate medication safety recommendations"""
        recommendations = []
        
        if contraindications:
            recommendations.append('Review contraindicated medications with physician')
        
        if interactions:
            recommendations.append('Monitor for drug interaction symptoms')
            recommendations.append('Consider timing medication doses appropriately')
        
        if warnings:
            recommendations.append('Follow proper dosing guidelines')
            recommendations.append('Monitor for side effects')
        
        recommendations.append('Maintain updated medication list')
        recommendations.append('Inform all healthcare providers of current medications')
        
        return recommendations
    
    def _analyze_single_vital(
        self, 
        vital_name: str, 
        value: float, 
        age: int, 
        gender: str
    ) -> Dict:
        """Analyze a single vital sign measurement"""
        ranges = self.vital_ranges.get(vital_name, {})
        
        # Determine appropriate range based on age
        if age >= 65:
            range_key = 'elderly'
        else:
            range_key = 'adult'
        
        if range_key not in ranges:
            range_key = 'normal'
        
        if range_key not in ranges:
            range_key = list(ranges.keys())[0]
        
        vital_range = ranges[range_key]
        
        # Analyze the value
        if value < vital_range['min']:
            status = 'LOW'
            severity = 'HIGH' if value < vital_range['min'] * 0.8 else 'MEDIUM'
            message = f"{vital_name.replace('_', ' ').title()} is below normal range"
        elif value > vital_range['max']:
            status = 'HIGH'
            severity = 'HIGH' if value > vital_range['max'] * 1.2 else 'MEDIUM'
            message = f"{vital_name.replace('_', ' ').title()} is above normal range"
        else:
            status = 'NORMAL'
            severity = 'NONE'
            message = f"{vital_name.replace('_', ' ').title()} is within normal range"
        
        return {
            'value': value,
            'status': status,
            'severity': severity,
            'message': message,
            'reference_range': f"{vital_range['min']}-{vital_range['max']}",
            'optimal_value': vital_range.get('optimal')
        }
    
    def _generate_vital_recommendations(
        self, 
        vital_name: str, 
        analysis: Dict, 
        medical_history: List[str]
    ) -> List[str]:
        """Generate recommendations based on vital sign analysis"""
        recommendations = []
        
        if analysis['status'] == 'HIGH':
            if vital_name == 'blood_pressure_systolic':
                recommendations.append('Monitor blood pressure regularly')
                recommendations.append('Consider lifestyle modifications (diet, exercise)')
                if analysis['severity'] == 'HIGH':
                    recommendations.append('Immediate medical evaluation recommended')
            elif vital_name == 'heart_rate':
                recommendations.append('Monitor heart rate and rhythm')
                recommendations.append('Avoid stimulants')
        
        elif analysis['status'] == 'LOW':
            if vital_name == 'blood_pressure_systolic':
                recommendations.append('Monitor for dizziness or fainting')
                recommendations.append('Ensure adequate hydration')
            elif vital_name == 'heart_rate':
                recommendations.append('Monitor for symptoms of bradycardia')
        
        return recommendations
    
    def _calculate_health_score(self, vital_analysis: Dict) -> float:
        """Calculate overall health score based on vital signs"""
        total_score = 0.0
        count = 0
        
        for vital_name, analysis in vital_analysis.items():
            if analysis['status'] == 'NORMAL':
                total_score += 100
            elif analysis['status'] in ['HIGH', 'LOW']:
                if analysis['severity'] == 'HIGH':
                    total_score += 30
                elif analysis['severity'] == 'MEDIUM':
                    total_score += 60
                else:
                    total_score += 80
            count += 1
        
        return total_score / max(count, 1)
    
    def _identify_critical_vital_combinations(self, vital_analysis: Dict) -> List[Dict]:
        """Identify critical combinations of vital signs"""
        critical_combinations = []
        
        # Check for shock-like presentation
        bp_systolic = vital_analysis.get('blood_pressure_systolic', {})
        heart_rate = vital_analysis.get('heart_rate', {})
        
        if (bp_systolic.get('status') == 'LOW' and 
            heart_rate.get('status') == 'HIGH'):
            critical_combinations.append({
                'combination': 'Hypotension with Tachycardia',
                'significance': 'May indicate shock or severe volume depletion',
                'urgency': 'CRITICAL',
                'action': 'Immediate medical evaluation required'
            })
        
        return critical_combinations
    
    def _determine_overall_vital_status(self, alerts: List[Dict]) -> str:
        """Determine overall vital signs status"""
        if not alerts:
            return 'NORMAL'
        
        critical_alerts = [a for a in alerts if a['severity'] == 'HIGH']
        if critical_alerts:
            return 'CRITICAL'
        
        medium_alerts = [a for a in alerts if a['severity'] == 'MEDIUM']
        if medium_alerts:
            return 'ABNORMAL'
        
        return 'BORDERLINE'
    
    def _analyze_single_lab_result(
        self, 
        test_name: str, 
        value: float, 
        age: int, 
        gender: str
    ) -> Dict:
        """Analyze a single laboratory result"""
        ranges = self.lab_ranges.get(test_name, {})
        
        # Determine appropriate range based on gender for certain tests
        gender_key = 'male' if gender == 'M' else 'female'
        
        if gender_key in ranges:
            range_data = ranges[gender_key]
        elif 'normal' in ranges:
            range_data = ranges['normal']
        else:
            range_data = list(ranges.values())[0]
        
        # Analyze the value
        if value < range_data['min']:
            status = 'LOW'
            severity = 'HIGH' if value < range_data['min'] * 0.7 else 'MEDIUM'
        elif value > range_data['max']:
            status = 'HIGH'
            severity = 'HIGH' if value > range_data['max'] * 1.3 else 'MEDIUM'
        else:
            status = 'NORMAL'
            severity = 'NONE'
        
        return {
            'value': value,
            'status': status,
            'severity': severity,
            'reference_range': f"{range_data['min']}-{range_data['max']} {range_data['unit']}",
            'unit': range_data['unit'],
            'clinical_significance': self._get_clinical_significance(test_name, status, severity)
        }
    
    def _get_clinical_significance(self, test_name: str, status: str, severity: str) -> str:
        """Get clinical significance of lab result"""
        if status == 'NORMAL':
            return 'Within normal limits'
        
        significance_map = {
            'glucose': {
                'HIGH': 'May indicate diabetes or prediabetes',
                'LOW': 'May indicate hypoglycemia'
            },
            'cholesterol_total': {
                'HIGH': 'Increased cardiovascular risk',
                'LOW': 'Generally not concerning'
            },
            'hemoglobin': {
                'HIGH': 'May indicate dehydration or polycythemia',
                'LOW': 'May indicate anemia'
            }
        }
        
        if test_name in significance_map and status in significance_map[test_name]:
            return significance_map[test_name][status]
        
        return f"Abnormal result - {status.lower()}"
    
    def _identify_lab_patterns(self, lab_analysis: Dict, medical_history: List[str]) -> List[str]:
        """Identify patterns in laboratory results"""
        patterns = []
        
        # Check for diabetic pattern
        glucose_result = lab_analysis.get('glucose')
        if glucose_result and glucose_result['status'] == 'HIGH':
            if 'diabetes' not in [h.lower() for h in medical_history]:
                patterns.append('Elevated glucose suggests possible diabetes - recommend HbA1c testing')
        
        # Check for anemia pattern
        hemoglobin_result = lab_analysis.get('hemoglobin')
        if hemoglobin_result and hemoglobin_result['status'] == 'LOW':
            patterns.append('Low hemoglobin suggests anemia - recommend iron studies and B12/folate levels')
        
        return patterns
    
    def _check_disease_markers(self, lab_analysis: Dict) -> List[str]:
        """Check for specific disease markers in lab results"""
        markers = []
        
        # This would be expanded with comprehensive disease marker analysis
        # For now, basic examples
        
        glucose_result = lab_analysis.get('glucose')
        if glucose_result and glucose_result['value'] > 200:
            markers.append('Glucose >200 mg/dL suggests diabetes mellitus')
        
        cholesterol_result = lab_analysis.get('cholesterol_total')
        if cholesterol_result and cholesterol_result['value'] > 240:
            markers.append('Total cholesterol >240 mg/dL indicates high cardiovascular risk')
        
        return markers
    
    def _generate_lab_follow_up_recommendations(
        self, 
        abnormal_results: List[Dict], 
        patterns: List[str]
    ) -> List[str]:
        """Generate follow-up recommendations based on lab results"""
        recommendations = []
        
        if abnormal_results:
            recommendations.append('Discuss abnormal results with primary care physician')
            
            high_severity = [r for r in abnormal_results if r['severity'] == 'HIGH']
            if high_severity:
                recommendations.append('Schedule follow-up appointment within 1-2 weeks')
            else:
                recommendations.append('Schedule routine follow-up appointment')
        
        if patterns:
            recommendations.append('Consider additional diagnostic testing based on patterns identified')
        
        return recommendations
    
    def _generate_overall_lab_assessment(
        self, 
        abnormal_results: List[Dict], 
        insights: List[str]
    ) -> str:
        """Generate overall assessment of laboratory results"""
        if not abnormal_results:
            return 'All laboratory results within normal limits'
        
        high_severity = len([r for r in abnormal_results if r['severity'] == 'HIGH'])
        medium_severity = len([r for r in abnormal_results if r['severity'] == 'MEDIUM'])
        
        if high_severity > 0:
            return f'Significant abnormalities detected requiring prompt medical attention ({high_severity} high priority)'
        elif medium_severity > 0:
            return f'Moderate abnormalities detected requiring follow-up ({medium_severity} moderate priority)'
        else:
            return 'Minor abnormalities detected for monitoring'
    
    # Additional helper methods would continue here...
    
    def _adjust_probability_for_demographics(
        self, 
        base_probability: float, 
        age: int, 
        gender: str, 
        history: List[str], 
        condition: str
    ) -> float:
        """Adjust probability based on patient demographics"""
        adjusted = base_probability
        
        # Age adjustments
        if condition == 'Myocardial Infarction' and age > 50:
            adjusted *= 1.2
        elif condition == 'Viral Infection' and age < 18:
            adjusted *= 1.3
        
        # Gender adjustments
        if condition == 'Myocardial Infarction' and gender == 'M':
            adjusted *= 1.1
        
        # History adjustments
        if any(h.lower() in condition.lower() for h in history):
            adjusted *= 1.5
        
        return min(adjusted, 0.95)
    
    def _calculate_symptom_specificity(self, symptoms: List[str], condition: str) -> float:
        """Calculate how specific symptoms are for a condition"""
        # This would use a comprehensive symptom-condition specificity database
        # For now, basic implementation
        return 0.8
    
    def _generate_medication_plan(self, diagnosis: str, patient_data: Dict, severity: str) -> List[Dict]:
        """Generate medication recommendations for diagnosis"""
        # This would access a comprehensive treatment database
        return [
            {
                'medication': 'Example Medication',
                'dosage': '10mg',
                'frequency': 'Once daily',
                'duration': '7 days',
                'purpose': 'Primary treatment'
            }
        ]
    
    def _generate_lifestyle_recommendations(self, diagnosis: str, patient_data: Dict) -> List[str]:
        """Generate lifestyle recommendations"""
        return [
            'Maintain regular exercise routine',
            'Follow balanced diet',
            'Ensure adequate sleep',
            'Stay hydrated'
        ]
    
    def _generate_monitoring_plan(self, diagnosis: str, severity: str, patient_data: Dict) -> List[Dict]:
        """Generate monitoring plan"""
        return [
            {
                'parameter': 'Symptoms',
                'frequency': 'Daily',
                'method': 'Patient self-assessment'
            }
        ]
    
    def _generate_follow_up_schedule(self, diagnosis: str, severity: str) -> List[Dict]:
        """Generate follow-up schedule"""
        if severity == 'HIGH':
            return [
                {'timeframe': '1 week', 'type': 'In-person visit'},
                {'timeframe': '2 weeks', 'type': 'Phone check-in'}
            ]
        else:
            return [
                {'timeframe': '2 weeks', 'type': 'Phone check-in'},
                {'timeframe': '1 month', 'type': 'In-person visit'}
            ]
    
    def _estimate_treatment_duration(self, diagnosis: str, severity: str, patient_data: Dict) -> str:
        """Estimate treatment duration"""
        if severity == 'HIGH':
            return '2-4 weeks'
        elif severity == 'MEDIUM':
            return '1-2 weeks'
        else:
            return '3-7 days'
    
    def _calculate_treatment_success_probability(
        self, 
        diagnosis: str, 
        patient_data: Dict, 
        severity: str
    ) -> float:
        """Calculate probability of treatment success"""
        base_probability = 0.8
        
        # Adjust based on age
        age = patient_data.get('age', 40)
        if age > 70:
            base_probability *= 0.9
        elif age < 18:
            base_probability *= 1.1
        
        # Adjust based on severity
        if severity == 'HIGH':
            base_probability *= 0.8
        elif severity == 'LOW':
            base_probability *= 1.1
        
        return min(base_probability, 0.95)
    
    def _suggest_alternative_treatments(self, diagnosis: str, patient_data: Dict) -> List[str]:
        """Suggest alternative treatment options"""
        return [
            'Physical therapy',
            'Dietary modifications',
            'Alternative medications if first-line treatment fails'
        ]


class ClinicalAlertEngine:
    """
    Real-time clinical alert system for critical conditions
    """
    
    def __init__(self):
        self.alert_thresholds = self._load_alert_thresholds()
    
    def process_real_time_alerts(self, patient_data: Dict) -> List[Dict]:
        """Process real-time clinical alerts"""
        alerts = []
        
        # Check vital signs alerts
        if 'vital_signs' in patient_data:
            vital_alerts = self._check_vital_alerts(patient_data['vital_signs'])
            alerts.extend(vital_alerts)
        
        # Check lab alerts
        if 'lab_results' in patient_data:
            lab_alerts = self._check_lab_alerts(patient_data['lab_results'])
            alerts.extend(lab_alerts)
        
        # Check medication alerts
        if 'medications' in patient_data:
            med_alerts = self._check_medication_alerts(patient_data['medications'])
            alerts.extend(med_alerts)
        
        return alerts
    
    def _load_alert_thresholds(self) -> Dict:
        """Load critical alert thresholds"""
        return {
            'blood_pressure_systolic': {'critical_high': 180, 'critical_low': 70},
            'heart_rate': {'critical_high': 150, 'critical_low': 40},
            'temperature': {'critical_high': 39.5, 'critical_low': 35.0},
            'oxygen_saturation': {'critical_low': 90}
        }
    
    def _check_vital_alerts(self, vital_signs: Dict) -> List[Dict]:
        """Check for critical vital sign alerts"""
        alerts = []
        
        for vital_name, value in vital_signs.items():
            if vital_name in self.alert_thresholds:
                thresholds = self.alert_thresholds[vital_name]
                
                if 'critical_high' in thresholds and value > thresholds['critical_high']:
                    alerts.append({
                        'type': 'CRITICAL_VITAL',
                        'parameter': vital_name,
                        'value': value,
                        'threshold': thresholds['critical_high'],
                        'severity': 'CRITICAL',
                        'message': f'Critical high {vital_name.replace("_", " ")}: {value}',
                        'action_required': 'Immediate medical intervention'
                    })
                
                if 'critical_low' in thresholds and value < thresholds['critical_low']:
                    alerts.append({
                        'type': 'CRITICAL_VITAL',
                        'parameter': vital_name,
                        'value': value,
                        'threshold': thresholds['critical_low'],
                        'severity': 'CRITICAL',
                        'message': f'Critical low {vital_name.replace("_", " ")}: {value}',
                        'action_required': 'Immediate medical intervention'
                    })
        
        return alerts
    
    def _check_lab_alerts(self, lab_results: Dict) -> List[Dict]:
        """Check for critical lab result alerts"""
        alerts = []
        
        # Critical glucose levels
        if 'glucose' in lab_results:
            glucose = lab_results['glucose']
            if glucose > 400:
                alerts.append({
                    'type': 'CRITICAL_LAB',
                    'parameter': 'glucose',
                    'value': glucose,
                    'severity': 'CRITICAL',
                    'message': f'Critical hyperglycemia: {glucose} mg/dL',
                    'action_required': 'Immediate diabetes management'
                })
            elif glucose < 50:
                alerts.append({
                    'type': 'CRITICAL_LAB',
                    'parameter': 'glucose',
                    'value': glucose,
                    'severity': 'CRITICAL',
                    'message': f'Severe hypoglycemia: {glucose} mg/dL',
                    'action_required': 'Immediate glucose administration'
                })
        
        return alerts
    
    def _check_medication_alerts(self, medications: List[Dict]) -> List[Dict]:
        """Check for medication-related alerts"""
        alerts = []
        
        # Check for high-risk medication combinations
        high_risk_combinations = [
            ['warfarin', 'aspirin'],
            ['metformin', 'contrast_dye']
        ]
        
        med_names = [med.get('name', '').lower() for med in medications]
        
        for combination in high_risk_combinations:
            if all(med in med_names for med in combination):
                alerts.append({
                    'type': 'MEDICATION_INTERACTION',
                    'medications': combination,
                    'severity': 'HIGH',
                    'message': f'High-risk combination: {" + ".join(combination)}',
                    'action_required': 'Review medication safety'
                })
        
        return alerts
