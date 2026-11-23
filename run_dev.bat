@echo off
start "StudyMate Backend" cmd /c call "%~dp0run_backend.bat"
start "StudyMate Frontend" cmd /c call "%~dp0run_frontend.bat"
echo StudyMate will be available at http://localhost:3000 once both servers are ready.
