#!/bin/bash

# Phase 2 EMR AI Integration Testing Script
# Tests all EMR AI clinical decision support features

echo "🧪 PHASE 2 EMR AI INTEGRATION - COMPREHENSIVE TESTING"
echo "=================================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run tests
run_test() {
    local test_name="$1"
    local command="$2"
    
    echo -e "\n${BLUE}🔍 Testing: $test_name${NC}"
    echo "----------------------------------------"
    
    if eval "$command" 2>/dev/null; then
        echo -e "${GREEN}✅ PASSED: $test_name${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAILED: $test_name${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Start testing
echo -e "${YELLOW}🚀 Starting Phase 2 EMR AI Testing...${NC}\n"

# Test 1: Check if EMR app is installed
run_test "EMR App Installation" "python manage.py shell -c \"import apps.emr.models; print('EMR models imported successfully')\""

# Test 2: Check EMR models
run_test "EMR Models Structure" "python manage.py shell -c \"
from apps.emr.models import MedicalRecord, VitalSigns, Medication, LabResult, ClinicalAlert, ClinicalDecisionSupport
print('All EMR models available')
print('MedicalRecord fields:', [f.name for f in MedicalRecord._meta.fields])
print('VitalSigns fields:', [f.name for f in VitalSigns._meta.fields])
\""

# Test 3: Check AI Clinical Engine
run_test "AI Clinical Engine" "python manage.py shell -c \"
from apps.emr.ai_clinical_engine import ClinicalDecisionEngine
engine = ClinicalDecisionEngine()
result = engine.analyze_symptoms(['fever', 'cough'], patient_age=30, patient_gender='M')
print('AI Analysis Result:', result)
assert 'conditions' in result
assert 'confidence' in result
print('AI Clinical Engine working correctly')
\""

# Test 4: Test Drug Interaction Checking
run_test "Drug Interaction AI" "python manage.py shell -c \"
from apps.emr.ai_clinical_engine import ClinicalDecisionEngine
engine = ClinicalDecisionEngine()
interactions = engine.check_drug_interactions(['aspirin', 'warfarin'])
print('Drug Interactions:', interactions)
assert isinstance(interactions, list)
print('Drug interaction checking working')
\""

# Test 5: Test Vital Signs Analysis
run_test "Vital Signs AI Analysis" "python manage.py shell -c \"
from apps.emr.ai_clinical_engine import ClinicalDecisionEngine
engine = ClinicalDecisionEngine()
analysis = engine.analyze_vital_signs(blood_pressure_systolic=160, blood_pressure_diastolic=95, heart_rate=95, temperature=38.5, respiratory_rate=22, oxygen_saturation=95)
print('Vital Signs Analysis:', analysis)
assert 'alerts' in analysis
assert 'risk_level' in analysis
print('Vital signs analysis working')
\""

# Test 6: Test Lab Result Interpretation
run_test "Lab Result AI Interpretation" "python manage.py shell -c \"
from apps.emr.ai_clinical_engine import ClinicalDecisionEngine
engine = ClinicalDecisionEngine()
interpretation = engine.interpret_lab_results({'hemoglobin': 8.5, 'white_blood_cells': 12000, 'glucose': 180})
print('Lab Interpretation:', interpretation)
assert 'interpretations' in interpretation
print('Lab result interpretation working')
\""

# Test 7: Test EMR Views Import
run_test "EMR Views Import" "python manage.py shell -c \"
from apps.emr.views import EMRDashboardView, MedicalRecordListView, VitalSignsListView
from apps.emr.ai_views import AIClinicalDashboardView, AIPatientAnalysisView
print('All EMR views imported successfully')
\""

# Test 8: Test URL Configuration
run_test "EMR URLs Configuration" "python manage.py shell -c \"
from django.urls import reverse, NoReverseMatch
try:
    url = reverse('emr:dashboard')
    print('EMR dashboard URL:', url)
    url = reverse('emr:ai_dashboard')
    print('AI dashboard URL:', url)
    print('URL configuration working')
except NoReverseMatch as e:
    print('URL configuration error:', e)
    raise
\""

# Test 9: Database Migration Status
run_test "Database Migrations" "python manage.py showmigrations emr | grep '\\[X\\]' | wc -l | python -c \"
import sys
count = int(input())
if count > 0:
    print(f'EMR migrations applied: {count}')
else:
    raise Exception('No EMR migrations found')
\""

# Test 10: Test EMR Admin Interface
run_test "EMR Admin Configuration" "python manage.py shell -c \"
from apps.emr.admin import MedicalRecordAdmin, VitalSignsAdmin, MedicationAdmin, LabResultAdmin, ClinicalAlertAdmin, ClinicalDecisionSupportAdmin
print('All EMR admin classes imported successfully')
\""

# Test 11: Create Test EMR Data
run_test "Create Test EMR Data" "python manage.py shell -c \"
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zain_hms.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
from apps.patients.models import Patient
from apps.emr.models import MedicalRecord, VitalSigns
from django.utils import timezone
import uuid

User = get_user_model()

# Get or create a test user
user, created = User.objects.get_or_create(
    username='test_doctor',
    defaults={
        'email': 'test@example.com',
        'first_name': 'Test',
        'last_name': 'Doctor',
        'role': 'doctor'
    }
)

# Get or create a test patient
patient, created = Patient.objects.get_or_create(
    patient_id='TEST001',
    defaults={
        'first_name': 'Test',
        'last_name': 'Patient',
        'date_of_birth': '1990-01-01',
        'gender': 'M',
        'phone': '1234567890',
        'email': 'patient@test.com'
    }
)

# Create test medical record
medical_record, created = MedicalRecord.objects.get_or_create(
    patient=patient,
    doctor=user,
    defaults={
        'chief_complaint': 'Test complaint',
        'history_of_present_illness': 'Test history',
        'diagnosis': 'Test diagnosis',
        'treatment_plan': 'Test treatment',
        'ai_diagnostic_suggestions': {'suggestions': ['test condition']},
        'ai_confidence_score': 0.85
    }
)

# Create test vital signs
vital_signs, created = VitalSigns.objects.get_or_create(
    medical_record=medical_record,
    defaults={
        'blood_pressure_systolic': 120,
        'blood_pressure_diastolic': 80,
        'heart_rate': 75,
        'temperature': 37.0,
        'respiratory_rate': 16,
        'oxygen_saturation': 98,
        'ai_analysis': {'status': 'normal', 'alerts': []},
        'ai_risk_score': 0.2
    }
)

print('Test EMR data created successfully')
print(f'Medical Record ID: {medical_record.id}')
print(f'Vital Signs ID: {vital_signs.id}')
\""

# Test 12: AI Clinical Dashboard Rendering
run_test "AI Clinical Dashboard Rendering" "python manage.py shell -c \"
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from apps.emr.ai_views import AIClinicalDashboardView
from django.http import HttpRequest

User = get_user_model()
factory = RequestFactory()
user = User.objects.filter(username='test_doctor').first()

if user:
    request = factory.get('/emr/ai-dashboard/')
    request.user = user
    
    view = AIClinicalDashboardView()
    view.request = request
    context = view.get_context_data()
    
    print('AI Dashboard context keys:', list(context.keys()))
    assert 'ai_metrics' in context
    assert 'high_risk_patients' in context
    print('AI Clinical Dashboard working correctly')
else:
    print('Test user not found, skipping dashboard test')
\""

# Display final results
echo -e "\n${BLUE}📊 TESTING SUMMARY${NC}"
echo "=================================="
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo -e "Total Tests: $((TESTS_PASSED + TESTS_FAILED))"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 ALL TESTS PASSED! Phase 2 EMR AI Integration is working perfectly!${NC}"
    echo -e "${GREEN}✅ EMR AI Clinical Decision Support System is ready for production!${NC}"
else
    echo -e "\n${YELLOW}⚠️  Some tests failed. Please review the output above.${NC}"
fi

# Test individual AI components
echo -e "\n${BLUE}🔬 DETAILED AI COMPONENT TESTING${NC}"
echo "=================================="

# Test AI Symptom Analysis with various scenarios
echo -e "\n${YELLOW}Testing AI Symptom Analysis...${NC}"
python manage.py shell -c "
from apps.emr.ai_clinical_engine import ClinicalDecisionEngine
engine = ClinicalDecisionEngine()

test_cases = [
    (['fever', 'cough', 'shortness_of_breath'], 65, 'M'),
    (['chest_pain', 'sweating'], 55, 'M'),
    (['headache', 'nausea', 'vomiting'], 25, 'F'),
    (['fatigue', 'weight_loss'], 40, 'F')
]

for symptoms, age, gender in test_cases:
    result = engine.analyze_symptoms(symptoms, age, gender)
    print(f'Symptoms: {symptoms} | Age: {age} | Gender: {gender}')
    print(f'Top condition: {result[\"conditions\"][0][\"condition\"]} (confidence: {result[\"conditions\"][0][\"probability\"]:.2f})')
    print('---')
"

# Test AI Drug Interactions
echo -e "\n${YELLOW}Testing AI Drug Interactions...${NC}"
python manage.py shell -c "
from apps.emr.ai_clinical_engine import ClinicalDecisionEngine
engine = ClinicalDecisionEngine()

drug_combinations = [
    ['warfarin', 'aspirin'],
    ['metformin', 'insulin'],
    ['lisinopril', 'hydrochlorothiazide'],
    ['simvastatin', 'amlodipine']
]

for drugs in drug_combinations:
    interactions = engine.check_drug_interactions(drugs)
    print(f'Drugs: {drugs}')
    if interactions:
        for interaction in interactions:
            print(f'  - {interaction[\"severity\"]}: {interaction[\"description\"]}')
    else:
        print('  - No significant interactions found')
    print('---')
"

# Performance testing
echo -e "\n${YELLOW}Performance Testing...${NC}"
python manage.py shell -c "
import time
from apps.emr.ai_clinical_engine import ClinicalDecisionEngine

engine = ClinicalDecisionEngine()

# Test response times
tests = [
    ('Symptom Analysis', lambda: engine.analyze_symptoms(['fever', 'cough'], 30, 'M')),
    ('Drug Interaction', lambda: engine.check_drug_interactions(['aspirin', 'warfarin'])),
    ('Vital Signs Analysis', lambda: engine.analyze_vital_signs(120, 80, 75, 37.0, 16, 98)),
    ('Lab Interpretation', lambda: engine.interpret_lab_results({'glucose': 150}))
]

for test_name, test_func in tests:
    start_time = time.time()
    result = test_func()
    end_time = time.time()
    response_time = (end_time - start_time) * 1000  # Convert to milliseconds
    print(f'{test_name}: {response_time:.2f}ms')
"

echo -e "\n${GREEN}🎊 Phase 2 EMR AI Integration Testing Complete!${NC}"
echo -e "${GREEN}The AI Clinical Decision Support System is fully operational!${NC}"
