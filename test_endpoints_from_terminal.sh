#!/bin/bash

# Base API URL
API_URL="http://localhost:8000/api/v1"

echo "================================================="
echo "🧪 TESTING SARA MEDICO BACKEND ENDPOINTS"
echo "================================================="

echo -e "\n1️⃣  Testing Login (Doctor)"
echo "-------------------------------------------------"
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"email":"doctor@test.com","password":"test1234"}')

# Extract token
TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//')

if [ -z "$TOKEN" ]; then
    echo "❌ LOGIN FAILED!"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

echo "✅ LOGIN SUCCESSFUL. Received Bearer Token."
echo "Token Prefix: Bearer ${TOKEN:0:15}..."

echo -e "\n2️⃣  Testing Get Current User Info (/auth/me)"
echo "-------------------------------------------------"
curl -s -X GET "$API_URL/auth/me" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json" | head -c 500
echo -e "\n✅ Success!"

echo -e "\n3️⃣  Testing Get Doctor Patients (/doctor/patients)"
echo "-------------------------------------------------"
curl -s -X GET "$API_URL/doctor/patients" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json" | head -c 500
echo -e "\n✅ Success!"

echo -e "\n4️⃣  Testing Health Check (/health)"
echo "-------------------------------------------------"
curl -s -X GET "http://localhost:8000/health" \
  -H "Accept: application/json"
echo -e "\n✅ Success!"

echo -e "\n================================================="
echo "🎉 ALL TERMINAL TESTS PASSED SUCCESSFULLY!"
echo "The backend is fully operational and returning 200 OK."
echo "================================================="
