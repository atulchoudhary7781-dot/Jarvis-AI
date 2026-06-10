@echo off
REM Start JARVIS Background Voice Service
REM This script runs JARVIS in the background with voice activation

setlocal enabledelayedexpansion

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

REM Navigate to the script directory
cd /d "%SCRIPT_DIR%"

REM Check if virtual environment exists
if not exist ".venv\Scripts\activate.bat" (
    echo Virtual environment not found. Please run setup_env.ps1 first.
    pause
    exit /b 1
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Start the background service
echo.
echo ========================================
echo JARVIS Background Voice Service
echo ========================================
echo.
echo Starting JARVIS voice activation service...
echo.
echo Listening for: "Hey Jarvis"
echo Lights: Enabled
echo.
echo Press Ctrl+C to stop the service
echo.

python jarvis_voice_service.py --start

pause
