#!/bin/bash

# OGTool - API Testing Script

API_URL="http://localhost:8000/api/v1"

echo "Testing OGTool API..."
echo ""

# Health check
echo "1. Health Check..."
curl -s $API_URL/../health | jq '.'
echo ""

# Register
echo "2. Registering test user..."
REGISTER_RESPONSE=$(curl -s -X POST $API_URL/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "full_name": "Test User",
    "organization_name": "Test Org"
  }')
echo $REGISTER_RESPONSE | jq '.'
echo ""

# Login
echo "3. Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST $API_URL/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }')
echo $LOGIN_RESPONSE | jq '.'
TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
echo ""

# Create keyword
echo "4. Creating keyword..."
curl -s -X POST $API_URL/keywords \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "keyword": "project management",
    "platform": "reddit",
    "priority": 80
  }' | jq '.'
echo ""

# List keywords
echo "5. Listing keywords..."
curl -s $API_URL/keywords \
  -H "Authorization: Bearer $TOKEN" | jq '.'
echo ""

echo "API tests complete!"
