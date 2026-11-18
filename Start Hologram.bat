@echo off
setlocal
cd /d "%~dp0"
if exist "%LOCALAPPDATA%\JarvisAmber\voice-v2\Scripts\python.exe" goto enhanced
where py >nul 2>nul
if errorlevel 1 goto plain
py -3 launch_hologram.py %*
goto done
:enhanced
"%LOCALAPPDATA%\JarvisAmber\voice-v2\Scripts\python.exe" launch_hologram.py %*
goto done
:plain
python launch_hologram.py %*
:done
if errorlevel 1 pause
endlocal
