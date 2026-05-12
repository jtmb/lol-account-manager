@echo off
REM League of Legends Account Manager - Windows Launcher

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.9+ from https://www.python.org/
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install/upgrade dependencies
echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install dependencies
    pause
    exit /b 1
)

REM Run the application
echo Starting League of Legends Account Manager...
python src/main.py

REM If something goes wrong, pause to show error
if %errorlevel% neq 0 (
    pause
)
