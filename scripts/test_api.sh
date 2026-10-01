#!/usr/bin/env bash
# ==============================================================================
# Agentic Controller Office — Local API Testing Script
# ==============================================================================

BASE_URL="http://localhost:8000"

echo "========================================================================"
echo "          VIRTUAL CONTROLLER OFFICE — FASTAPI LOCAL TEST SUITE          "
echo "========================================================================"
echo ""

# 1. Health Check
echo "1️⃣ Testing Health Check Endpoint (/api/health)..."
curl -s -X GET "${BASE_URL}/api/health" | jq . || curl -s -X GET "${BASE_URL}/api/health"
echo -e "\n------------------------------------------------------------------------\n"

# 2. Submit Audit Request
echo "2️⃣ Submitting Controlling Audit Request (/api/audit/submit)..."
AUDIT_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/audit/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Audit Q3 logistics cost overruns across European subsidiaries and recommend corrective actions.",
    "user_id": "controller_admin"
  }')
echo "${AUDIT_RESPONSE}" | jq . || echo "${AUDIT_RESPONSE}"
echo -e "\n------------------------------------------------------------------------\n"

# 3. Fetch Agent Execution Trajectory
echo "3️⃣ Fetching Real-Time Agent Trajectory Logs (/api/trajectory)..."
curl -s -X GET "${BASE_URL}/api/trajectory" | jq . || curl -s -X GET "${BASE_URL}/api/trajectory"
echo -e "\n------------------------------------------------------------------------\n"

# 4. Approve HITL Gate
echo "4️⃣ Testing Human-In-The-Loop Approval Gate (/api/hitl/approve)..."
HITL_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/hitl/approve" \
  -H "Content-Type: application/json" \
  -d '{
    "run_id": "run_q3_audit_001",
    "approved": true,
    "user_feedback": "Approved contractual fuel surcharge cap enforcement."
  }')
echo "${HITL_RESPONSE}" | jq . || echo "${HITL_RESPONSE}"
echo -e "\n------------------------------------------------------------------------\n"

# 5. External Serper Research Test
echo "5️⃣ Testing External Hybrid Serper Research Endpoint (/api/research/serper)..."
SERPER_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/research/serper" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "European logistics fuel surcharge trends Q3 2026 DB Schenker FedEx DHL"
  }')
echo "${SERPER_RESPONSE}" | jq . || echo "${SERPER_RESPONSE}"
echo -e "\n========================================================================\n"
echo "✅ Local API testing sequence completed."
