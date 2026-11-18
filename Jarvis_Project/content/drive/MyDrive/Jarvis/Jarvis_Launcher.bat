@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 goto plain
py -3 "..\..\..\..\run_jarvis.py" %*
goto done
:plain
python "..\..\..\..\run_jarvis.py" %*
:done
if errorlevel 1 pause
endlocal
