@echo off
REM League of Legends Account Manager - Windows Launcher
setlocal enabledelayedexpansion

REM Colors and formatting
color 0A
cls

echo.
echo ====================================================
echo   League of Legends Account Manager
echo ====================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python is not installed or not in PATH.
    echo.
    echo Two options:
    echo.
    echo Option 1 - Automatic Installation (RECOMMENDED):
    echo   Press any key to download and install Python 3.11...
    echo.
    echo Option 2 - Manual Installation:
    echo   1. Visit https://www.python.org/downloads/
    echo   2. Download Python 3.11 or later
    echo   3. Run the installer
    echo   4. CHECK "Add Python to PATH" during install
    echo   5. Restart your computer
    echo   6. Double-click this file again
    echo.
    pause

    REM Download Python installer
    echo.
    echo [*] Downloading Python 3.11...
    REM Using curl to download (built-in on Windows 10+)
    if not exist python-installer.exe (
        curl -L -o python-installer.exe https://www.python.org/ftp/python/3.11.8/python-3.11.8-amd64.exe
        if !errorlevel! neq 0 (
            echo [!] Failed to download Python. Please install manually from https://www.python.org/
            pause
            exit /b 1
        )
    )

    echo [*] Running Python installer...
    echo     Make sure to CHECK "Add Python to PATH" during installation!
    echo.
    echo     Installer will open in 5 seconds...
    timeout /t 5

    REM Run installer with options to add to PATH
    python-installer.exe /quiet PrependPath=1
    if !errorlevel! neq 0 (
        python-installer.exe
        if !errorlevel! neq 0 (
            echo [!] Python installation failed
            pause
            exit /b 1
        )
    )

    echo [*] Python installed! Restarting...
    timeout /t 3

    REM Restart this script
    call %0
    exit /b 0
)

echo [+] Python found: 
python --version
echo.

REM Create virtual environment
if not exist venv (
    echo [*] Creating virtual environment...
    python -m venv venv
    if !errorlevel! neq 0 (
        echo [!] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [+] Virtual environment created
)

REM Activate virtual environment
call venv\Scripts\activate.bat
if !errorlevel! neq 0 (
    echo [!] Failed to activate virtual environment
    pause
    exit /b 1
)

REM Install dependencies
echo.
echo [*] Installing dependencies (this may take 1-2 minutes)...
pip install --quiet -r requirements.txt
if !errorlevel! neq 0 (
    echo [!] Failed to install dependencies
    echo     Trying again with more verbose output...
    pip install -r requirements.txt
    if !errorlevel! neq 0 (
        echo [!] Dependency installation failed
        pause
        exit /b 1
    )
)
echo [+] Dependencies installed

REM Run the application
echo.
echo [*] Starting League of Legends Account Manager...
echo.
python src/main.py

REM If something goes wrong, pause to show error
if !errorlevel! neq 0 (
    echo.
    echo [!] Application error occurred
    pause
)

endlocal
