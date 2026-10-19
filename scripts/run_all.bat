@echo off
echo =================================================================
echo AI TECH CONSULTANT: 12-HOUR CAPSTONE MVP MASTER DEMO
echo =================================================================

cd /d "%~dp0\.."

echo.
echo [STEP 1/4] Starting Task 1 Knowledge Brain in background...
start /B .venv\Scripts\python.exe -m uvicorn task1_knowledge_brain.app.main:app --host 127.0.0.1 --port 8001
timeout /t 3 /nobreak >nul

echo.
echo [STEP 2/4] Running Task 2 TypeScript Inbox Agent...
cd task2_inbox_agent
call npm test
cd ..

echo.
echo [STEP 3/4] Running Task 3 Meeting-to-Scope CLI...
.venv\Scripts\python.exe task3_meeting_to_scope/app/cli.py generate-scope --file evals/fixtures/task3_transcripts/initial_discovery.txt --client "Apex Legal Directory Corp" --title "Enterprise Legal Portal"

echo.
echo [STEP 4/4] Running Master Evaluations Suite across Tasks 1, 2, 3...
.venv\Scripts\python.exe evals/run_all_evals.py

echo.
echo =================================================================
echo MASTER INTEGRATION DEMO COMPLETE!
echo =================================================================
