@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title JARVIS - Enhanced voice
if not defined LOCALAPPDATA goto missing
set "VENV=%LOCALAPPDATA%\JarvisAmber\voice-v2"
set "VEXE=%VENV%\Scripts\python.exe"
if exist "%VEXE%" goto verify
set "ENGINE="
where py >nul 2>nul
if errorlevel 1 goto plain
for %%V in (3.12 3.13 3.11 3.10) do (
  py -%%V -c "import struct,sys;sys.exit(0 if struct.calcsize('P')==8 else 1)" >nul 2>nul
  if not errorlevel 1 (
    set "ENGINE=py"
    set "VERSION=-%%V"
    goto confirm
  )
)
:plain
python -c "import struct,sys;sys.exit(0 if sys.version_info[:2] in [(3,10),(3,11),(3,12),(3,13)] and struct.calcsize('P')==8 else 1)" >nul 2>nul
if errorlevel 1 goto missing
set "ENGINE=python"
set "VERSION="
:confirm
echo This installs the optional neural speech engine in your local user folder.
echo The first enhanced run downloads about 94 MB of model data, once.
echo The neural voice is generated on this PC, not by a TTS service.
choice /c YN /m "Set up the enhanced voice on this PC"
if errorlevel 2 exit /b 0
%ENGINE% %VERSION% -m venv "%VENV%"
if errorlevel 1 goto failed
goto install
:verify
"%VEXE%" -c "from importlib.metadata import version;import sys;sys.exit(0 if version('kokoro-onnx')=='0.6.1' else 1)" >nul 2>nul
if not errorlevel 1 goto run
:install
"%VEXE%" -m pip install -r "%~dp0requirements-voice.txt"
if errorlevel 1 goto failed
:run
"%VEXE%" "%~dp0launch_hologram.py" %*
if errorlevel 1 goto failed
exit /b 0
:missing
echo Enhanced voice needs 64-bit Python 3.10 to 3.13. Python 3.12 is recommended.
echo Or run "Start Hologram.bat" for the lighter device-voice version.
goto failed
:failed
pause
exit /b 1
