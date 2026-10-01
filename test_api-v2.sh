#!/usr/bin/env bash
# ==============================================================================
# Agentic Controller Office — Local API Testing Script (v2)
# ==============================================================================

BASE_URL="http://localhost:8000"

echo "========================================================================"
echo "          VIRTUAL CONTROLLER OFFICE — FASTAPI LOCAL TEST SUITE (v2)     "
echo "========================================================================"
echo ""

# 1. Health Check
echo "1️⃣ Testing Health Check Endpoint (/api/health)..."
curl -s -X GET "${BASE_URL}/api/health" | jq . || curl -s -X GET "${BASE_URL}/api/health"
echo -e "\n------------------------------------------------------------------------\n"

# 2. Submit Audit Request
echo "2️⃣ Submitting Controlling Audit Request (/api/audit/request)..."
AUDIT_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/audit/request" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Audit Q3 logistics cost overruns across European subsidiaries and recommend corrective actions.",
    "user_id": "controller_admin"
  }')
echo "${AUDIT_RESPONSE}" | jq . || echo "${AUDIT_RESPONSE}"
echo -e "\n------------------------------------------------------------------------\n"

# 3. Fetch Agent Execution Trajectory
echo "3️⃣ Fetching Real-Time Agent Trajectory Logs (/api/audit/trajectory)..."
curl -s -X GET "${BASE_URL}/api/audit/trajectory" | jq . || curl -s -X GET "${BASE_URL}/api/audit/trajectory"
echo -e "\n------------------------------------------------------------------------\n"

# 4. Approve HITL Gate
echo "4️⃣ Testing Human-In-The-Loop Approval Gate (/api/audit/hitl/respond)..."
TASK_ID=$(echo "${AUDIT_RESPONSE}" | jq -r '.task_id // "task_sample"')
HITL_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/audit/hitl/respond" \
  -H "Content-Type: application/json" \
  -d "{
    \"task_id\": \"${TASK_ID}\",
    \"approved\": true,
    \"feedback\": \"Approved contractual fuel surcharge cap enforcement.\"
  }")
echo "${HITL_RESPONSE}" | jq . || echo "${HITL_RESPONSE}"
echo -e "\n------------------------------------------------------------------------\n"

# 5. External Hybrid Serper Research Test
echo "5️⃣ Testing External Hybrid Serper Research Handler..."
SERPER_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/audit/request" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Research European logistics fuel surcharge trends Q3 2026 DB Schenker FedEx DHL"
  }')
echo "${SERPER_RESPONSE}" | jq . || echo "${SERPER_RESPONSE}"
echo -e "\n------------------------------------------------------------------------\n"

# 6. Agent 0 Meta-UI Enhancer Test
echo "6️⃣ Testing Agent 0 Meta-UI Enhancer Endpoint (/api/agent/enhance-ui)..."
ENHANCE_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/agent/enhance-ui" \
  -H "Content-Type: application/json" \
  -d '{
    "feature_request": "Add fuel surcharge variance gauge widget"
  }')
echo "${ENHANCE_RESPONSE}" | jq . || echo "${ENHANCE_RESPONSE}"
echo -e "\n========================================================================\n"
echo "✅ Local API v2 testing sequence completed."
