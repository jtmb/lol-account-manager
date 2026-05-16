@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"

echo.
echo [*] Building LoL Account Manager EXE...
echo.

if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found. Run this script from project root.
    pause
    exit /b 1
)

set "VENV_PY=venv\Scripts\python.exe"
if not exist "%VENV_PY%" (
    echo [*] Creating virtual environment...
    py -3 -m venv venv || python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

echo [*] Installing dependencies...
"%VENV_PY%" -m pip install --upgrade pip
"%VENV_PY%" -m pip install -r requirements.txt
"%VENV_PY%" -m pip install pyinstaller
if errorlevel 1 (
    echo [ERROR] Failed to install build dependencies.
    pause
    exit /b 1
)

echo [*] Cleaning previous build artifacts...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [*] Running PyInstaller from spec...
"%VENV_PY%" -m PyInstaller ^
  --noconfirm ^
  --clean ^
    lol_account_manager.spec

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Build complete.
echo EXE location: %CD%\dist\LoL Account Manager.exe
echo.
pause
