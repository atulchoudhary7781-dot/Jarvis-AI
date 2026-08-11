# setup_voice_activation.ps1 - Setup JARVIS Voice Activation
# Run as Administrator

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "JARVIS Voice Activation Setup" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Please right-click and select 'Run as Administrator'" -ForegroundColor Yellow
    pause
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
& .\.venv\Scripts\Activate.ps1

# Install dependencies
Write-Host ""
Write-Host "Installing required packages..." -ForegroundColor Green

$packages = @(
    "pyaudio",
    "phue",
    "lifxlan",
    "pyserial",
    "pywin32"
)

foreach ($package in $packages) {
    Write-Host "Installing $package..." -ForegroundColor Cyan
    pip install $package -q
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Warning: Could not install $package (optional)" -ForegroundColor Yellow
    }
}

# Create configuration file if it doesn't exist
if (-not (Test-Path "jarvis_config.json")) {
    Write-Host ""
    Write-Host "Creating configuration file..." -ForegroundColor Green
    Write-Host "Edit jarvis_config.json to customize wake words and light settings"
}

# Setup Windows scheduled task
Write-Host ""
Write-Host "Setting up Windows scheduled task for auto-startup..." -ForegroundColor Green

$python_exe = (Get-Command python).Source
$script_path = (Get-Item "jarvis_voice_service.py").FullName

Write-Host ""
Write-Host "Options:" -ForegroundColor Yellow
Write-Host "1. Install auto-startup task (JARVIS starts automatically)" -ForegroundColor Cyan
Write-Host "2. Skip auto-startup (run manually)" -ForegroundColor Cyan

$choice = Read-Host "Enter your choice (1-2)"

if ($choice -eq "1") {
    Write-Host "Creating scheduled task..." -ForegroundColor Green
    
    $taskName = "JARVIS Background Service"
    $taskExists = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    
    if ($taskExists) {
        Write-Host "Task already exists. Removing old task..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    }
    
    # Create task
    $action = New-ScheduledTaskAction -Execute $python_exe -Argument "$script_path --start"
    $trigger = New-ScheduledTaskTrigger -AtStartup
    $principal = New-ScheduledTaskPrincipal -UserID (whoami) -LogonType ServiceAccount -RunLevel Highest
    
    Register-ScheduledTask -Action $action -Trigger $trigger -Principal $principal -TaskName $taskName -Description "JARVIS Background Voice Service" -Force | Out-Null
    
    Write-Host "✅ Auto-startup task created successfully!" -ForegroundColor Green
    Write-Host "JARVIS will now start automatically on system startup" -ForegroundColor Green
}
else {
    Write-Host "Skipping auto-startup setup" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Edit jarvis_config.json to configure your lights" -ForegroundColor Cyan
Write-Host "2. Run: python jarvis_voice_service.py --start" -ForegroundColor Cyan
Write-Host "3. Say 'Hey Jarvis' near your microphone" -ForegroundColor Cyan
Write-Host "4. Watch your lights turn on!" -ForegroundColor Cyan
Write-Host ""
Write-Host "For more info, see VOICE_ACTIVATION_GUIDE.md" -ForegroundColor Green
Write-Host ""

pause
