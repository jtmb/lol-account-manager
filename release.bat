@echo off
setlocal

cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0release.ps1" %*
if errorlevel 1 (
  echo.
  echo [ERROR] Release automation failed.
  exit /b 1
)

exit /b 0
