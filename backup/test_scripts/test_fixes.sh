#!/bin/bash

echo "Testing Hospital Management System Endpoints..."

# Start server in background
/home/mehedi/Projects/zain_hms/venv/bin/python /home/mehedi/Projects/zain_hms/manage.py runserver 8002 &
SERVER_PID=$!

# Wait for server to start
sleep 3

echo "Testing previously failing endpoints:"

echo -n "Emergency page: "
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8002/emergency/
echo

echo -n "Nurses page: "
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8002/nurses/
echo

echo -n "Pharmacy bills: "
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8002/pharmacy/bills/
echo

echo -n "Laboratory page: "
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8002/laboratory/
echo

echo -n "Dashboard page: "
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8002/dashboard/
echo

echo "Testing static files:"
echo -n "Logo: "
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8002/static/images/logo.png
echo

echo -n "Favicon: "
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8002/static/images/favicon.ico
echo

# Stop server
kill $SERVER_PID
echo "Test completed."
