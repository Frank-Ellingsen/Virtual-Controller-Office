#!/usr/bin/env bash
# ==============================================================================
# Virtual Controller Office — FastAPI End-to-End API Test Suite (v3)
# ==============================================================================

BASE_URL="http://localhost:8000"

echo "========================================================================"
echo "          VIRTUAL CONTROLLER OFFICE — FASTAPI TEST SUITE (v3)          "
echo "========================================================================"
echo ""

# 1. Health Check
echo "1️⃣ Testing Health Check Endpoint (/api/health)..."
curl -s -X GET "${BASE_URL}/api/health" | jq . || curl -s -X GET "${BASE_URL}/api/health"
echo -e "
------------------------------------------------------------------------
"

# 2. Query Initial Close Stage Statuses from DuckDB
echo "2️⃣ Fetching Initial Monthly Close Stage Statuses (/api/close/stages/close_2026_10)..."
curl -s -X GET "${BASE_URL}/api/close/stages/close_2026_10" | jq . || curl -s -X GET "${BASE_URL}/api/close/stages/close_2026_10"
echo -e "
------------------------------------------------------------------------
"

# 3. Manually Approve Stage 1 in DuckDB
echo "3️⃣ Submitting Manual Controller Approval for Stage 1 (/api/close/stage/approve)..."
STAGE1_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/close/stage/approve"   -H "Content-Type: application/json"   -d '{
    "task_id": "close_2026_10",
    "stage_id": 1,
    "approved": true,
    "controller_comments": "Pre-close PO cutoffs verified against ERP records.",
    "reviewer": "controller_admin"
  }')
echo "${STAGE1_RESPONSE}" | jq . || echo "${STAGE1_RESPONSE}"
echo -e "
------------------------------------------------------------------------
"

# 4. Agent 0 UI Enhancer Test
echo "4️⃣ Testing Agent 0 Meta-Builder UI Enhancer (/api/agent/enhance-ui)..."
ENHANCE_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/agent/enhance-ui"   -H "Content-Type: application/json"   -d '{
    "feature_request": "Add a live fuel surcharge variance gauge widget for EU Central carriers."
  }')
echo "${ENHANCE_RESPONSE}" | jq . || echo "${ENHANCE_RESPONSE}"
echo -e "
------------------------------------------------------------------------
"

# 5. Fetch Execution Trajectory Logs
echo "5️⃣ Fetching Real-Time Agent Trajectory Logs (/api/trajectory)..."
curl -s -X GET "${BASE_URL}/api/trajectory" | jq . || curl -s -X GET "${BASE_URL}/api/trajectory"
echo -e "
========================================================================
"
echo "✅ Stage-by-Stage API testing sequence completed."
