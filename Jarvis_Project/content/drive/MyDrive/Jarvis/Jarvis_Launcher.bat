@echo off
setlocal
cd /d "%~dp0"
if /i "%~1"=="--classic" goto pick
if exist "%LOCALAPPDATA%\JarvisAmber\voice-v2\Scripts\python.exe" goto enhanced
:pick
where py >nul 2>nul
if errorlevel 1 goto plain
py -3 "..\..\..\..\run_jarvis.py" %*
goto done
:enhanced
"%LOCALAPPDATA%\JarvisAmber\voice-v2\Scripts\python.exe" "..\..\..\..\run_jarvis.py" %*
goto done
:plain
python "..\..\..\..\run_jarvis.py" %*
:done
if errorlevel 1 pause
endlocal
