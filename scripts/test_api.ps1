# ==============================================================================
# Virtual Controller Office — PowerShell API Integration Test Harness
# ==============================================================================

$BaseUrl = "http://localhost:8000"

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "          VIRTUAL CONTROLLER OFFICE -- LOCAL API TEST SUITE            " -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Health Check
Write-Host "1. Testing Health Check Endpoint ($BaseUrl/api/health)..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$BaseUrl/api/health" -Method Get
    $health | ConvertTo-Json
    Write-Host " Health Check: OK" -ForegroundColor Green
} catch {
    Write-Host " Failed to connect to $BaseUrl. Is 'python server.py' running?" -ForegroundColor Red
    exit 1
}

Write-Host "------------------------------------------------------------------------"

# 2. Submit Audit Request
Write-Host "2. Submitting Controlling Audit Request ($BaseUrl/api/audit/submit)..." -ForegroundColor Yellow
$auditPayload = @{
    prompt = "Audit Q3 logistics cost overruns across European subsidiaries and recommend corrective actions."
    user_id = "controller_admin"
} | ConvertTo-Json

$auditRes = Invoke-RestMethod -Uri "$BaseUrl/api/audit/submit" -Method Post -Body $auditPayload -ContentType "application/json"
$auditRes | ConvertTo-Json
$taskId = $auditRes.task_id
Write-Host " Task Received: $taskId" -ForegroundColor Green

Write-Host "------------------------------------------------------------------------"

# 3. Fetch Execution Trajectory
Write-Host "3. Fetching Real-Time Agent Trajectory Logs ($BaseUrl/api/trajectory)..." -ForegroundColor Yellow
$trajRes = Invoke-RestMethod -Uri "$BaseUrl/api/trajectory" -Method Get
$trajRes.logs | Select-Object -Last 3 | Format-Table -AutoSize
Write-Host " Trajectory Fetched" -ForegroundColor Green

Write-Host "------------------------------------------------------------------------"

# 4. Approve HITL Gate
Write-Host "4. Testing Human-In-The-Loop Approval Gate ($BaseUrl/api/hitl/approve)..." -ForegroundColor Yellow
$hitlPayload = @{
    task_id = $taskId
    approved = $true
    user_feedback = "Approved contractual fuel surcharge cap enforcement."
} | ConvertTo-Json

$hitlRes = Invoke-RestMethod -Uri "$BaseUrl/api/hitl/approve" -Method Post -Body $hitlPayload -ContentType "application/json"
$hitlRes | ConvertTo-Json
Write-Host " HITL Gate Approved" -ForegroundColor Green

Write-Host "------------------------------------------------------------------------"

# 5. External Serper Research Test
Write-Host "5. Testing Hybrid External Research Endpoint ($BaseUrl/api/research/serper)..." -ForegroundColor Yellow
$serperPayload = @{
    query = "European logistics fuel surcharge trends Q3 2026 DB Schenker FedEx DHL"
    num_results = 3
} | ConvertTo-Json

$serperRes = Invoke-RestMethod -Uri "$BaseUrl/api/research/serper" -Method Post -Body $serperPayload -ContentType "application/json"
$serperRes | ConvertTo-Json -Depth 4
Write-Host " Research Handler Verified" -ForegroundColor Green

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host " Local API testing sequence completed successfully!" -ForegroundColor Green
Write-Host "========================================================================" -ForegroundColor Cyan
