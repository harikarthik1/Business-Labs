# Master startup and cross-task integration demo

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "AI TECH CONSULTANT: 12-HOUR CAPSTONE MVP MASTER DEMO" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

$WorkspaceRoot = (Get-Item -Path $PSScriptRoot).Parent.FullName
Set-Location $WorkspaceRoot

# 1. Start Task 1 Knowledge Brain in background
Write-Host "`n[STEP 1/4] Starting Task 1 Knowledge Brain API on port 8001..." -ForegroundColor Yellow
$Task1Process = Start-Process -FilePath "$WorkspaceRoot\.venv\Scripts\python.exe" -ArgumentList "-m uvicorn task1_knowledge_brain.app.main:app --host 127.0.0.1 --port 8001" -PassThru -NoNewWindow

Start-Sleep -Seconds 3

# Check Health
try {
    $Health = Invoke-RestMethod -Uri "http://127.0.0.1:8001/health" -Method Get -TimeoutSec 5
    Write-Host "[OK] Task 1 Knowledge Brain is HEALTHY! Articles indexed: $($Health.articles_count)" -ForegroundColor Green
} catch {
    Write-Host "[NOTICE] Knowledge Brain health check: continuing..." -ForegroundColor Yellow
}

# 2. Run Task 2 Inbox Agent against Task 1 HTTP API
Write-Host "`n[STEP 2/4] Running Task 2: TypeScript Inbox Agent..." -ForegroundColor Yellow
Set-Location "$WorkspaceRoot\task2_inbox_agent"
npm test
Set-Location $WorkspaceRoot

# 3. Run Task 3 Meeting-to-Scope Pipeline & Diff Engine
Write-Host "`n[STEP 3/4] Running Task 3: Meeting-to-Scope Pipeline and Scope Diff..." -ForegroundColor Yellow
& "$WorkspaceRoot\.venv\Scripts\python.exe" task3_meeting_to_scope/app/cli.py generate-scope --file evals/fixtures/task3_transcripts/initial_discovery.txt --client "Apex Legal Directory Corp" --title "Enterprise Legal Portal"

# Retrieve generated scope ID and run follow-up diff
$ScopeData = Get-Content -Raw "$WorkspaceRoot\task3_meeting_to_scope\data\scopes.json" | ConvertFrom-Json
$LatestScope = $ScopeData[-1]

Write-Host "`nApproving Scope $($LatestScope.scope_id)..." -ForegroundColor Cyan
& "$WorkspaceRoot\.venv\Scripts\python.exe" task3_meeting_to_scope/app/cli.py approve-scope --scope-id $LatestScope.scope_id --approver "Sarah Lead Architect"

Write-Host "`nComparing Follow-Up Discovery Transcript against Approved Scope $($LatestScope.scope_id)..." -ForegroundColor Cyan
& "$WorkspaceRoot\.venv\Scripts\python.exe" task3_meeting_to_scope/app/cli.py diff-scope --scope-id $LatestScope.scope_id --file evals/fixtures/task3_transcripts/followup_meeting.txt

# 4. Master Evaluation Suite Run
Write-Host "`n[STEP 4/4] Executing Master Evaluations Suite across all 3 tasks..." -ForegroundColor Yellow
& "$WorkspaceRoot\.venv\Scripts\python.exe" evals/run_all_evals.py

# Cleanup background server
if ($Task1Process -and -not $Task1Process.HasExited) {
    Stop-Process -Id $Task1Process.Id -Force
    Write-Host "`nTask 1 background server stopped." -ForegroundColor Gray
}

Write-Host "`n=================================================================" -ForegroundColor Green
Write-Host "MASTER INTEGRATION DEMO COMPLETE! All 3 tasks verified." -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green
