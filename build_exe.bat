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
if exist LoLAccountManager.spec del /q LoLAccountManager.spec

echo [*] Running PyInstaller...
set "ICON_ARG="
set "DATA_ARG="
if exist "assets\icon.ico" set "ICON_ARG=--icon assets\icon.ico"
if exist "assets\icon.ico" set "DATA_ARG=--add-data assets\icon.ico;assets"
"%VENV_PY%" -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --name "LoLAccountManager" ^
  --windowed ^
    %ICON_ARG% ^
    %DATA_ARG% ^
  --collect-all pywinauto ^
  src\main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Build complete.
echo EXE location: %CD%\dist\LoLAccountManager\LoLAccountManager.exe
echo.
pause
