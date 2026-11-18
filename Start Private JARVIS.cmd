@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title JARVIS - Private Windows session
echo JARVIS can request Calculator, Notepad and Paint. Nothing opens without a Windows confirmation.
echo Use your own unlocked Windows account. Do not run as administrator.
if exist "%LOCALAPPDATA%\JarvisAmber\voice-v2\Scripts\python.exe" goto neural
where py >nul 2>nul
if errorlevel 1 goto plain
py -3 "%~dp0launch_hologram.py" --desktop --browser-tab --port 0
goto end
:plain
python "%~dp0launch_hologram.py" --desktop --browser-tab --port 0
goto end
:neural
"%LOCALAPPDATA%\JarvisAmber\voice-v2\Scripts\python.exe" "%~dp0launch_hologram.py" --desktop --browser-tab --port 0
:end
if errorlevel 1 pause
