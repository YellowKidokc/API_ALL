@echo off
setlocal EnableDelayedExpansion
pushd "%~dp0" || (
  echo ERROR: Could not open EVIDENCE folder.
  pause
  exit /b 1
)

echo =========================================================================
echo  FAITH THROUGH PHYSICS - RUST AUTOMATION TIMER & INBOX DAEMON
echo =========================================================================
echo.

set /p IDLE_MINS="Enter Inactivity Trigger in Minutes (default: 30): "
if "%IDLE_MINS%"=="" set "IDLE_MINS=30"

echo.
echo Starting Rust Watcher Daemon on INBOX (Idle Trigger: %IDLE_MINS% mins)...
echo Press Ctrl+C at any time to stop.
echo.

"%~dp0SCRIPTS\pipeline_watcher.exe" --idle-mins %IDLE_MINS% --root "%~dp0."
set "EXIT_CODE=%ERRORLEVEL%"

popd
pause
exit /b %EXIT_CODE%
