#!/bin/bash

# Simplified Phase 2 EMR AI Test - Core Components Only
echo "🧪 PHASE 2 EMR AI - CORE COMPONENT TEST"
echo "===================================="

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test counter
PASSED=0
FAILED=0

test_component() {
    local name="$1"
    local command="$2"
    
    echo -e "\n${BLUE}Testing: $name${NC}"
    if eval "$command" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ PASSED: $name${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAILED: $name${NC}"
        ((FAILED++))
    fi
}

# Core tests
test_component "EMR Models Import" "python manage.py shell -c 'from apps.emr.models import MedicalRecord, VitalSigns, ClinicalAlert, ClinicalDecisionSupport'"

test_component "AI Clinical Engine" "python manage.py shell -c 'from apps.emr.ai_clinical_engine import ClinicalDecisionEngine; engine = ClinicalDecisionEngine(); result = engine.analyze_symptoms([\"fever\"], 30, \"M\"); assert \"conditions\" in result'"

test_component "AI Views Import" "python manage.py shell -c 'from apps.emr.ai_views import AIClinicalDashboardView'"

test_component "EMR URLs" "python manage.py shell -c 'from django.urls import reverse; reverse(\"emr:dashboard\")'"

test_component "Database Migrations" "python manage.py showmigrations emr | grep -q '\\[X\\]'"

test_component "AI Dashboard Context" "python manage.py shell -c 'from django.test import RequestFactory; from apps.emr.ai_views import AIClinicalDashboardView; from tenants.models import Tenant; from django.contrib.auth import get_user_model; User = get_user_model(); factory = RequestFactory(); user = User.objects.first(); request = factory.get(\"/\"); request.user = user; request.tenant = Tenant.objects.first(); view = AIClinicalDashboardView(); view.request = request; context = view.get_context_data(); assert \"ai_metrics\" in context'"

# Summary
echo -e "\n${BLUE}SUMMARY${NC}"
echo "========"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 ALL CORE TESTS PASSED!${NC}"
    echo -e "${GREEN}Phase 2 EMR AI Integration is ready!${NC}"
else
    echo -e "\n${RED}Some tests failed.${NC}"
fi
