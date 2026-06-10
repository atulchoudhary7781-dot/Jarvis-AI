@echo off
REM Create Windows Scheduled Task for JARVIS Background Service
REM This allows JARVIS to start automatically on system startup

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

echo.
echo ========================================
echo JARVIS Auto-Startup Setup
echo ========================================
echo.
echo This will create a Windows scheduled task
echo to run JARVIS voice service at startup.
echo.

python jarvis_voice_service.py --task

if %ERRORLEVEL% EQU 0 (
    echo.
    echo SUCCESS: JARVIS will now start automatically on system startup!
    echo.
) else (
    echo.
    echo ERROR: Failed to create scheduled task.
    echo Please run this script as Administrator.
    echo.
)

pause
