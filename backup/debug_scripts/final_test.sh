#!/bin/bash

echo "=== Final Hospital Management System Test ==="
echo "Testing all previously problematic endpoints..."

# Function to test endpoint
test_endpoint() {
    local url=$1
    local name=$2
    echo -n "Testing $name: "
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    
    if [ "$response" = "200" ]; then
        echo "✅ SUCCESS ($response)"
    elif [ "$response" = "302" ]; then
        echo "⚠️  REDIRECT ($response) - Likely authentication required"
    elif [ "$response" = "500" ]; then
        echo "❌ INTERNAL SERVER ERROR ($response)"
    else
        echo "⚠️  STATUS: $response"
    fi
}

# Start server silently in background
echo "Starting Django server..."
/home/mehedi/Projects/zain_hms/venv/bin/python /home/mehedi/Projects/zain_hms/manage.py runserver 8003 > /dev/null 2>&1 &
SERVER_PID=$!

# Wait for server to start
sleep 4

echo ""
echo "=== Previously Failing Endpoints ==="
test_endpoint "http://127.0.0.1:8003/emergency/" "Emergency Department"
test_endpoint "http://127.0.0.1:8003/nurses/" "Nurses Management"
test_endpoint "http://127.0.0.1:8003/pharmacy/bills/" "Pharmacy Bills"
test_endpoint "http://127.0.0.1:8003/laboratory/" "Laboratory"

echo ""
echo "=== Working Endpoints (for comparison) ==="
test_endpoint "http://127.0.0.1:8003/dashboard/" "Dashboard"
test_endpoint "http://127.0.0.1:8003/patients/" "Patients"
test_endpoint "http://127.0.0.1:8003/appointments/" "Appointments"
test_endpoint "http://127.0.0.1:8003/billing/" "Billing"
test_endpoint "http://127.0.0.1:8003/reports/" "Reports"

echo ""
echo "=== Static Files ==="
test_endpoint "http://127.0.0.1:8003/static/images/logo.png" "Logo"
test_endpoint "http://127.0.0.1:8003/static/images/favicon.ico" "Favicon"

# Stop server
echo ""
echo "Stopping test server..."
kill $SERVER_PID 2>/dev/null

echo ""
echo "=== Test Summary ==="
echo "✅ = Working correctly"
echo "⚠️  = Redirects (likely authentication-protected)"
echo "❌ = Server errors (need fixing)"
echo ""
echo "Test completed!"
