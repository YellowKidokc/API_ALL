@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0SET_WEBSHARE_CREDENTIALS.ps1"
if errorlevel 1 (
  echo.
  echo Setup did not complete.
  pause
)
