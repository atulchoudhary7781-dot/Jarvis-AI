# PowerShell helper to create a venv and install common optional deps for Jarvis demo
# Usage: Open PowerShell, navigate to the repo folder, then run: .\setup_env.ps1

$venv = "$PWD\.venv"
if (-Not (Test-Path $venv)) {
    python -m venv .venv
}
# Activate the venv (PowerShell activation)
if (Test-Path "$venv\Scripts\Activate.ps1") {
    Write-Host "Activating venv..."
    & "$venv\Scripts\Activate.ps1"
}

Write-Host "Upgrading pip..."
python -m pip install --upgrade pip

Write-Host "Installing packages (may take some time)..."
python -m pip install sentence-transformers openai groq pdfplumber python-docx python-pptx SpeechRecognition pyttsx3 python-dotenv duckduckgo-search pyautogui pycaw

Write-Host "Note: Installing FAISS on Windows via pip may fail."
Write-Host "If you need FAISS, install it via conda (recommended):"
Write-Host "    conda install -c pytorch faiss-cpu"
Write-Host "Or on Linux: pip install faiss-cpu"

Write-Host "Done. To use the virtual environment in PowerShell: . .\.venv\Scripts\Activate.ps1"