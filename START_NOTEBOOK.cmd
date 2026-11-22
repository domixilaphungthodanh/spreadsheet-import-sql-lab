@echo off
cd /d "%~dp0"
py -3.12 --version >nul 2>&1
if errorlevel 1 (
  python run_import.py --notebook %*
) else (
  py -3.12 run_import.py --notebook %*
)
if errorlevel 1 exit /b 1
pause
