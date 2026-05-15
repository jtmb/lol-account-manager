# League of Legends Account Manager - PowerShell Launcher
# Right-click > Run with PowerShell if run.bat doesn't work

param(
    [switch]$SkipPythonCheck = $false
)

# Set console colors
$host.UI.RawUI.BackgroundColor = "Black"
$host.UI.RawUI.ForegroundColor = "Green"
Clear-Host

Write-Host @"
========================================
  League of Legends Account Manager
========================================
"@

# Check if Python is installed
Write-Host "[*] Checking for Python..."
$pythonPath = $null

# Try to find Python in PATH
try {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        $pythonPath = $python.Source
        Write-Host "[+] Python found: $pythonPath"
        & python --version
    }
} catch {
    # Python not found, will attempt installation
}

# If Python not found, offer to install
if (-not $pythonPath) {
    Write-Host "[!] Python is not installed or not in PATH."
    Write-Host ""
    Write-Host "Downloading and installing Python 3.11..."
    Write-Host ""

    # Create temp directory for installer
    $tempDir = "$env:TEMP\LoLPythonSetup"
    if (-not (Test-Path $tempDir)) {
        New-Item -ItemType Directory -Path $tempDir | Out-Null
    }

    $installerPath = "$tempDir\python-3.11.8-amd64.exe"

    # Download Python
    if (-not (Test-Path $installerPath)) {
        Write-Host "[*] Downloading Python 3.11..."
        try {
            $url = "https://www.python.org/ftp/python/3.11.8/python-3.11.8-amd64.exe"
            Invoke-WebRequest -Uri $url -OutFile $installerPath -UseBasicParsing
            Write-Host "[+] Download complete"
        } catch {
            Write-Host "[!] Failed to download Python: $_"
            Write-Host ""
            Write-Host "Please install Python manually:"
            Write-Host "  1. Visit https://www.python.org/downloads/"
            Write-Host "  2. Download Python 3.11 or later"
            Write-Host "  3. Run the installer"
            Write-Host "  4. CHECK 'Add Python to PATH' during install"
            Write-Host "  5. Restart your computer"
            Write-Host "  6. Run this script again"
            Read-Host "Press Enter to exit"
            exit 1
        }
    }

    # Run installer
    Write-Host "[*] Running Python installer..."
    Write-Host ""
    Write-Host "IMPORTANT: When the installer appears, CHECK 'Add Python to PATH'"
    Write-Host ""
    Write-Host "Starting installer in 5 seconds..."
    Start-Sleep -Seconds 5

    & $installerPath /quiet PrependPath=1
    if ($LASTEXITCODE -ne 0) {
        # Try interactive mode if quiet install fails
        Write-Host "[*] Trying interactive installer..."
        & $installerPath
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[!] Python installation failed"
            Read-Host "Press Enter to exit"
            exit 1
        }
    }

    Write-Host "[+] Python installed!"
    Write-Host "[*] Restarting in 3 seconds..."
    Start-Sleep -Seconds 3

    # Restart the script
    & powershell.exe -ExecutionPolicy Bypass -File $PSCommandPath
    exit $LASTEXITCODE
}

Write-Host ""

# Check if running from correct directory
if (-not (Test-Path "requirements.txt")) {
    Write-Host "[!] Error: requirements.txt not found"
    Write-Host "    Make sure you're running this from the project folder"
    Read-Host "Press Enter to exit"
    exit 1
}

# Create virtual environment
if (-not (Test-Path "venv")) {
    Write-Host "[*] Creating virtual environment..."
    & python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[!] Failed to create virtual environment"
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "[+] Virtual environment created"
}

# Activate virtual environment
Write-Host "[*] Activating virtual environment..."
& .\venv\Scripts\Activate.ps1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] Failed to activate virtual environment"
    Read-Host "Press Enter to exit"
    exit 1
}

# Install dependencies
Write-Host ""
Write-Host "[*] Installing dependencies (this may take 1-2 minutes)..."
& pip install --quiet -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] Failed to install dependencies. Retrying with verbose output..."
    & pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[!] Dependency installation failed"
        Read-Host "Press Enter to exit"
        exit 1
    }
}
Write-Host "[+] Dependencies installed"

# Run the application
Write-Host ""
Write-Host "[*] Starting League of Legends Account Manager..."
Write-Host ""

$python = Join-Path $PSScriptRoot "venv\Scripts\python.exe"
$appLog = Join-Path $env:TEMP "LoLAccountManager\app-run.log"
$appLogDir = Split-Path -Parent $appLog
if (-not (Test-Path $appLogDir)) {
    New-Item -ItemType Directory -Path $appLogDir | Out-Null
}
if (Test-Path $python) {
    & $python -X faulthandler -m src.main *> $appLog
} else {
    & python -X faulthandler -m src.main *> $appLog
}

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[!] Application error occurred"
    Write-Host "[!] Log saved to: $appLog"
    if (Test-Path $appLog) {
        Write-Host ""
        Write-Host "----- Last 80 log lines -----"
        Get-Content -LiteralPath $appLog -Tail 80
    }
    Read-Host "Press Enter to exit"
}

exit $LASTEXITCODE
