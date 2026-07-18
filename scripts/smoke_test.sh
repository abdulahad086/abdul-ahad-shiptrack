#!/bin/bash
set -e

API_URL="http://localhost:8000"
API_KEY="local-dev-key"

echo "=== Running ShipTrack Smoke Tests ==="

# 1. GET /health
echo "Testing GET /health..."
curl -s -f -o /dev/null -w "Status: %{http_code}\n" "$API_URL/health"

# 2. POST /applications (No Auth - Expect 401)
echo "Testing POST /applications (No Auth)..."
curl -s -w "Status: %{http_code}\n" -X POST "$API_URL/applications" \
  -H "Content-Type: application/json" \
  -d '{"name": "test-app", "repo_url": "https://github.com/test/app"}'

# 3. POST /applications (With Auth - Expect 201)
echo "Testing POST /applications (With Auth)..."
APP_RESP=$(curl -s -w "\nStatus: %{http_code}" -X POST "$API_URL/applications" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"name": "checkout-service", "repo_url": "https://github.com/acme/checkout-service"}')
echo "$APP_RESP"

APP_ID=$(echo "$APP_RESP" | head -n 1 | grep -o '"id":[0-9]*' | cut -d: -f2)
echo "Created App ID: $APP_ID"

# 4. GET /applications (Expect 200)
echo "Testing GET /applications..."
curl -s -w "\nStatus: %{http_code}\n" "$API_URL/applications"

# 5. POST /deployments (With Auth, v1.0.0 - Expect 201)
echo "Testing POST /deployments (v1.0.0 succeeded)..."
DEP1_RESP=$(curl -s -w "\nStatus: %{http_code}" -X POST "$API_URL/deployments" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d "{\"application_id\": $APP_ID, \"version\": \"1.0.0\", \"environment\": \"prod\", \"status\": \"succeeded\"}")
echo "$DEP1_RESP"

# 6. POST /deployments (With Auth, v2.0.0 - Expect 201)
echo "Testing POST /deployments (v2.0.0 succeeded)..."
DEP2_RESP=$(curl -s -w "\nStatus: %{http_code}" -X POST "$API_URL/deployments" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d "{\"application_id\": $APP_ID, \"version\": \"2.0.0\", \"environment\": \"prod\", \"status\": \"succeeded\"}")
echo "$DEP2_RESP"

DEP2_ID=$(echo "$DEP2_RESP" | head -n 1 | grep -o '"id":[0-9]*' | cut -d: -f2)
echo "Created Deployment ID to rollback: $DEP2_ID"

# 7. GET /deployments (Expect 200)
echo "Testing GET /deployments..."
curl -s -w "\nStatus: %{http_code}\n" "$API_URL/deployments"

# 8. GET /deployments/{id} (Expect 200)
echo "Testing GET /deployments/$DEP2_ID..."
curl -s -w "\nStatus: %{http_code}\n" "$API_URL/deployments/$DEP2_ID"

# 9. POST /deployments/{id}/rollback (Expect 201)
echo "Testing POST /deployments/$DEP2_ID/rollback..."
ROLLBACK_RESP=$(curl -s -w "\nStatus: %{http_code}" -X POST "$API_URL/deployments/$DEP2_ID/rollback" \
  -H "X-API-Key: $API_KEY")
echo "$ROLLBACK_RESP"

echo "=== Smoke Tests Completed ==="
