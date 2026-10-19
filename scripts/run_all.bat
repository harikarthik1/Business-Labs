@echo off
echo =================================================================
echo TASK 1: KNOWLEDGE BRAIN — FASTAPI / RAG MASTER DEMO
echo =================================================================

cd /d "%~dp0\.."

echo.
echo [STEP 1/3] Starting Knowledge Brain API server in background on port 8001...
start /B .venv\Scripts\python.exe -m uvicorn task1_knowledge_brain.app.main:app --host 127.0.0.1 --port 8001
timeout /t 3 /nobreak >nul

echo.
echo [STEP 2/3] Running Task 1 Unit and Integration Pytest Suite...
.venv\Scripts\python.exe -m pytest task1_knowledge_brain/tests/

echo.
echo [STEP 3/3] Running Task 1 Evaluations & Model Comparison...
.venv\Scripts\python.exe evals/run_all_evals.py

echo.
echo =================================================================
echo TASK 1 DEMO & VERIFICATION COMPLETE!
echo =================================================================
