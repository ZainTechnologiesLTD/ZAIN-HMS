#!/bin/bash
# quick_hospital_access.sh
# Quick access script for super admin to access hospital modules

echo "🏥 HMS SUPER ADMIN - HOSPITAL MODULE ACCESS"
echo "============================================="

cd /home/mehedi/Projects/zain_hms

echo ""
echo "Available Hospital: Test Hospital (ID: 3262662)"
echo "Database: hospital_3262662"
echo ""

echo "🔗 HOSPITAL MODULE DIRECT ACCESS LINKS:"
echo "========================================"

echo ""
echo "📊 Dashboard:"
echo "   http://3262662.localhost:8000/dashboard/"

echo ""
echo "👥 Patients Management:"
echo "   http://3262662.localhost:8000/patients/"

echo ""
echo "👨‍⚕️ Doctors Management:"
echo "   http://3262662.localhost:8000/doctors/"

echo ""
echo "📅 Appointments:"
echo "   http://3262662.localhost:8000/appointments/"

echo ""
echo "🧪 Laboratory:"
echo "   http://3262662.localhost:8000/laboratory/"

echo ""
echo "💊 Pharmacy:"
echo "   http://3262662.localhost:8000/pharmacy/"

echo ""
echo "📸 Radiology:"
echo "   http://3262662.localhost:8000/radiology/"

echo ""
echo "💰 Billing:"
echo "   http://3262662.localhost:8000/billing/"

echo ""
echo "📋 EMR (Electronic Medical Records):"
echo "   http://3262662.localhost:8000/emr/"

echo ""
echo "🏥 IPD (In-Patient Department):"
echo "   http://3262662.localhost:8000/ipd/"

echo ""
echo "🚨 Emergency:"
echo "   http://3262662.localhost:8000/emergency/"

echo ""
echo "👩‍⚕️ Nurses:"
echo "   http://3262662.localhost:8000/nurses/"

echo ""
echo "📊 Reports:"
echo "   http://3262662.localhost:8000/reports/"

echo ""
echo "🤖 AI-ENHANCED MODULES:"
echo "======================="

echo ""
echo "🎯 AI Scheduling Dashboard:"
echo "   http://3262662.localhost:8000/appointments/ai/dashboard/"

echo ""
echo "🧠 Clinical AI Dashboard:"
echo "   http://3262662.localhost:8000/emr/ai/dashboard/"

echo ""
echo "💡 AI Billing Dashboard:"
echo "   http://3262662.localhost:8000/billing/ai/dashboard/"

echo ""
echo "⚠️  IMPORTANT NOTES:"
echo "==================="
echo "1. Each hospital has its own database (hospital_3262662)"
echo "2. You must access modules via hospital subdomain URLs"
echo "3. Super admin can access any hospital's modules"
echo "4. Main system database contains only tenant management"

echo ""
echo "🚀 TO START THE SERVER:"
echo "======================"
echo "python manage.py runserver"

echo ""
echo "Then open these URLs in your browser to access hospital modules."
echo "============================================="
