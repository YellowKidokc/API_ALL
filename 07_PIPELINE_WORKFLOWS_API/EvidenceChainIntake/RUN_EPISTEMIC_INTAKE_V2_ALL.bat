@echo off
setlocal
pushd "%~dp0" || (
  echo ERROR: Could not open this intake folder.
  pause
  exit /b 1
)
call "%~dp0SETUP_RUNTIME_FOLDERS.bat"

echo WARNING: This runs THREE API calls for EVERY eligible INBOX document.
python "%~dp0SCRIPTS\daily_api_preflight.py"
if errorlevel 1 (
  echo Daily API gate failed. No files were processed.
  popd
  pause
  exit /b 1
)
call "%~dp0SCRIPTS\LOGS\daily-api-route.cmd"
python "%~dp0SCRIPTS\epistemic_intake_v2.py" --all --limit %DAILY_API_MAX_FILES% --workers %DAILY_API_WORKERS%
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" echo One or more files failed. Failed originals remain in INBOX.
popd
pause
exit /b %EXIT_CODE%
