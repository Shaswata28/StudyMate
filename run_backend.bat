@echo off
echo ===================================================
echo Starting StudyMate Backend (FastAPI on Port 8000)
echo ===================================================
cd /d "%~dp0backend"
call venv\Scripts\activate
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
pause
