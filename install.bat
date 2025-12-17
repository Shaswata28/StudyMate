@echo off
REM Windows batch file to run the dependency installation script
echo Running dependency installation script...
python install_dependencies.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Installation encountered errors. Please check the output above.
    pause
    exit /b %ERRORLEVEL%
)
echo.
echo Installation completed successfully!
pause
