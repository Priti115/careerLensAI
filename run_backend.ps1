$ErrorActionPreference = "Stop"

$venvPython = ".\.venv\Scripts\python.exe"
$venvOk = $false
$pythonLauncher = Get-Command python -ErrorAction SilentlyContinue
$pythonArgs = @()

if (-not $pythonLauncher) {
    $pythonLauncher = Get-Command py -ErrorAction SilentlyContinue
    $pythonArgs = @("-3")
}

if (-not $pythonLauncher) {
    throw "Python is not installed. Install Python 3.11 or 3.12, then run this script again."
}

if (Test-Path $venvPython) {
    & $venvPython --version | Out-Null
    $venvOk = ($LASTEXITCODE -eq 0)
}

if (-not $venvOk -and (Test-Path ".venv")) {
    Write-Host "Existing .venv is broken. Removing it..."
    try {
        Remove-Item -LiteralPath ".venv" -Recurse -Force
    }
    catch {
        throw "Could not remove the broken .venv. Close terminals/editors using it, delete .venv manually, then rerun .\run_backend.ps1"
    }
}

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating virtual environment..."
    & $pythonLauncher.Source @pythonArgs -m venv .venv
}

Write-Host "Installing dependencies..."
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r requirements.txt

Write-Host "Starting CareerLensAI API..."
& $venvPython -m uvicorn app:app --host 127.0.0.1 --port 8000
