# ==============================================================================
# run_all.ps1 — Task 1: Knowledge Brain Startup & Verification Demo
# ==============================================================================

Write-Host '=================================================================' -ForegroundColor Cyan
Write-Host 'TASK 1: KNOWLEDGE BRAIN — FASTAPI / RAG MASTER DEMO' -ForegroundColor Cyan
Write-Host '=================================================================' -ForegroundColor Cyan

$WorkspaceRoot = (Get-Item -Path $PSScriptRoot).Parent.FullName
Set-Location $WorkspaceRoot

# 1. Start Task 1 Knowledge Brain in background
Write-Host ''
Write-Host '[STEP 1/3] Starting Knowledge Brain API server on port 8001...' -ForegroundColor Yellow
$Task1Process = Start-Process -FilePath "$WorkspaceRoot\.venv\Scripts\python.exe" `
    -ArgumentList "-m uvicorn task1_knowledge_brain.app.main:app --host 127.0.0.1 --port 8001" `
    -PassThru -NoNewWindow

Start-Sleep -Seconds 3

# Check Health
try {
    $Health = Invoke-RestMethod -Uri "http://127.0.0.1:8001/health" -Method Get -TimeoutSec 5
    Write-Host "[OK] Knowledge Brain is HEALTHY! Articles indexed: $($Health.articles_count)" -ForegroundColor Green
} catch {
    Write-Host '[NOTICE] Health check waiting for initialization...' -ForegroundColor Yellow
}

# 2. Run Task 1 Unit & Integration Tests
Write-Host ''
Write-Host '[STEP 2/3] Running Task 1 Pytest Suite...' -ForegroundColor Yellow
& "$WorkspaceRoot\.venv\Scripts\python.exe" -m pytest task1_knowledge_brain/tests/

# 3. Master Evaluation Suite Run
Write-Host ''
Write-Host '[STEP 3/3] Executing Task 1 Evaluation Suite and Model Comparison...' -ForegroundColor Yellow
& "$WorkspaceRoot\.venv\Scripts\python.exe" evals/run_all_evals.py

# Cleanup background server
if ($Task1Process -and -not $Task1Process.HasExited) {
    Stop-Process -Id $Task1Process.Id -Force
    Write-Host ''
    Write-Host 'Knowledge Brain background server stopped.' -ForegroundColor Gray
}

Write-Host ''
Write-Host '=================================================================' -ForegroundColor Green
Write-Host 'TASK 1 DEMO AND VERIFICATION COMPLETE!' -ForegroundColor Green
Write-Host '=================================================================' -ForegroundColor Green
