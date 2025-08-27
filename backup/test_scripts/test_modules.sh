#!/bin/bash

echo "=== Testing All Dashboard Modules ==="

# Start server in background
/home/mehedi/Projects/zain_hms/venv/bin/python /home/mehedi/Projects/zain_hms/manage.py runserver 8004 > /dev/null 2>&1 &
SERVER_PID=$!

# Wait for server to start
sleep 4

echo ""
echo "=== Main Modules (from sidebar) ==="

echo -n "Dashboard: "
curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8004/dashboard/" 2>/dev/null
echo

echo -n "Patients: "
curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8004/patients/" 2>/dev/null
echo

echo -n "Appointments: "
curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8004/appointments/" 2>/dev/null
echo

echo -n "Doctors: "
curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8004/doctors/" 2>/dev/null
echo

echo -n "Nurses: "
curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8004/nurses/" 2>/dev/null
echo

echo -n "Emergency: "
curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8004/emergency/" 2>/dev/null
echo

echo -n "Billing: "
curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8004/billing/" 2>/dev/null
echo

echo -n "Pharmacy: "
curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8004/pharmacy/bills/" 2>/dev/null
echo

echo -n "Laboratory: "
curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8004/laboratory/" 2>/dev/null
echo

echo -n "Reports: "
curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8004/reports/" 2>/dev/null
echo

echo ""
echo "=== Administrative Modules ==="

echo -n "User Management: "
curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8004/auth/users/" 2>/dev/null
echo

echo -n "System Settings: "
curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8004/dashboard/settings/" 2>/dev/null
echo

echo -n "Activity Logs: "
curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8004/dashboard/activity-logs/" 2>/dev/null
echo

# Stop server
kill $SERVER_PID 2>/dev/null

echo ""
echo "=== Status Code Legend ==="
echo "200 = ✅ Working (loads content)"
echo "302 = ⚠️  Redirect (authentication required)"
echo "404 = ❌ Not Found"
echo "500 = ❌ Server Error"
