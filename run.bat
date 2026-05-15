@echo off
REM League of Legends Account Manager - Windows Launcher
setlocal enableextensions enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"

if not defined LOL_KEEP_OPEN (
    start "League of Legends Account Manager" cmd /k "set LOL_KEEP_OPEN=1&& cd /d %~dp0 && call run.bat __KEEP_OPEN"
    exit /b 0
)

if /I "%~1"=="__KEEP_OPEN" shift

if not defined LOL_STAGED (
    set "PATH_PREFIX=%SCRIPT_DIR:~0,2%"
    if /I "!PATH_PREFIX!"=="\\" (
        echo [*] Detected network/WSL path.
        echo [*] Staging project to local Windows temp for reliable execution...
        call :stage_and_relaunch
        exit /b %errorlevel%
    )
)

pushd "%SCRIPT_DIR%" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Could not access project directory:
    echo %SCRIPT_DIR%
    echo If running from WSL path, copy project to a Windows drive and try again.
    pause
    exit /b 1
)

set "PYTHON_EXE="
set "DOWNLOAD_DIR=%TEMP%\LoLAccountManager"
if not exist "%DOWNLOAD_DIR%" mkdir "%DOWNLOAD_DIR%" >nul 2>&1
set "INSTALLER=%DOWNLOAD_DIR%\python-installer.exe"
set "PYTHON_URL=https://www.python.org/ftp/python/3.11.8/python-3.11.8-amd64.exe"

REM Colors and formatting
color 0A
cls

echo.
echo ====================================================
echo   League of Legends Account Manager
echo ====================================================
echo.

call :find_python
if not defined PYTHON_EXE (
    echo [ERROR] Python is not installed or not in PATH.
    echo.
    echo This launcher can install Python automatically.
    echo Press any key to continue.
    echo.
    pause

    echo.
    echo [*] Downloading Python 3.11...
    if exist "%INSTALLER%" del /f /q "%INSTALLER%" >nul 2>&1

    call :download_python
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to download Python installer.
        echo Please install manually from https://www.python.org/downloads/
        pause
        exit /b 1
    )

    echo [*] Running Python installer...
    echo     This may take a minute.

    "%INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1 Include_pip=1
    if !errorlevel! neq 0 (
        "%INSTALLER%"
        if !errorlevel! neq 0 (
            echo [ERROR] Python installation failed
            pause
            exit /b 1
        )
    )

    call :find_python
    if not defined PYTHON_EXE (
        echo [ERROR] Python installed but could not be detected in this session.
        echo Please close this window and run run.bat again.
        pause
        exit /b 1
    )
)

echo [+] Python found:
"%PYTHON_EXE%" --version
echo.

if not exist requirements.txt (
    echo [ERROR] requirements.txt not found.
    echo Make sure run.bat is in the project folder.
    pause
    exit /b 1
)

if not exist venv (
    echo [*] Creating virtual environment...
    "%PYTHON_EXE%" -m venv venv
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [+] Virtual environment created
)

set "VENV_PYTHON=%CD%\venv\Scripts\python.exe"
if not exist "%VENV_PYTHON%" (
    echo [ERROR] Virtual environment python not found:
    echo %VENV_PYTHON%
    pause
    exit /b 1
)

set "VENV_PYTHONW=%CD%\venv\Scripts\pythonw.exe"
if not exist "%VENV_PYTHONW%" set "VENV_PYTHONW=%VENV_PYTHON%"
set "APP_LOG=%DOWNLOAD_DIR%\app-run.log"

REM Install dependencies
echo.
echo [*] Installing dependencies (this may take 1-2 minutes)...
"%VENV_PYTHON%" -m pip install --quiet -r requirements.txt
if !errorlevel! neq 0 (
    echo [ERROR] Failed to install dependencies
    echo     Trying again with more verbose output...
    "%VENV_PYTHON%" -m pip install -r requirements.txt
    if !errorlevel! neq 0 (
        echo [ERROR] Dependency installation failed
        pause
        exit /b 1
    )
)
echo [+] Dependencies installed

REM Run the application
echo.
echo [*] Starting League of Legends Account Manager...
echo.
"%VENV_PYTHON%" -X faulthandler -m src.main > "%APP_LOG%" 2>&1

if !errorlevel! neq 0 (
    echo.
    echo [ERROR] Application error occurred
    echo [!] Log saved to:
    echo %APP_LOG%
    if exist "%APP_LOG%" (
        echo.
        echo ----- Last 80 log lines -----
        powershell -NoProfile -Command "Get-Content -LiteralPath '%APP_LOG%' -Tail 80"
        start "" notepad.exe "%APP_LOG%"
    )
    pause
    exit /b 1
)

popd >nul 2>&1
endlocal
pause
exit /b 0

:stage_and_relaunch
set "STAGE_ROOT=%TEMP%\LoLAccountManager\workspace"
if exist "%STAGE_ROOT%" rmdir /s /q "%STAGE_ROOT%" >nul 2>&1
mkdir "%STAGE_ROOT%" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Could not create staging directory:
    echo %STAGE_ROOT%
    pause
    exit /b 1
)

robocopy "%SCRIPT_DIR%" "%STAGE_ROOT%" /MIR /NFL /NDL /NJH /NJS /NP /XD .git venv __pycache__ /XF *.pyc >nul
if errorlevel 8 (
    echo [ERROR] Failed to copy project files to staging directory.
    pause
    exit /b 1
)

echo [*] Relaunching from local folder:
echo     %STAGE_ROOT%
cmd /c "set LOL_STAGED=1&& cd /d \"%STAGE_ROOT%\" && call run.bat"
exit /b %errorlevel%

:download_python
where curl >nul 2>&1
if %errorlevel% equ 0 (
    curl -fL "%PYTHON_URL%" -o "%INSTALLER%"
    if %errorlevel% equ 0 if exist "%INSTALLER%" exit /b 0
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "try { Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%INSTALLER%' -UseBasicParsing; exit 0 } catch { exit 1 }"
if %errorlevel% equ 0 if exist "%INSTALLER%" exit /b 0

where bitsadmin >nul 2>&1
if %errorlevel% equ 0 (
    bitsadmin /transfer pyDownload /download /priority normal "%PYTHON_URL%" "%INSTALLER%" >nul 2>&1
    if %errorlevel% equ 0 if exist "%INSTALLER%" exit /b 0
)

exit /b 1

:find_python
set "PYTHON_EXE="

where py >nul 2>&1
if %errorlevel% equ 0 (
    for /f "usebackq delims=" %%I in (`py -3 -c "import sys; print(sys.executable)" 2^>nul`) do set "PYTHON_EXE=%%I"
)

if not defined PYTHON_EXE (
    where python >nul 2>&1
    if %errorlevel% equ 0 (
        for /f "usebackq delims=" %%I in (`where python`) do (
            set "PYTHON_EXE=%%I"
            goto :found_python
        )
    )
)

if not defined PYTHON_EXE if exist "%LocalAppData%\Programs\Python\Python311\python.exe" set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python311\python.exe"
if not defined PYTHON_EXE if exist "%LocalAppData%\Programs\Python\Python310\python.exe" set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python310\python.exe"
if not defined PYTHON_EXE if exist "%ProgramFiles%\Python311\python.exe" set "PYTHON_EXE=%ProgramFiles%\Python311\python.exe"

:found_python
exit /b 0
