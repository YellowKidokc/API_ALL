@echo off
setlocal
pushd "%~dp0" || (
  echo ERROR: Could not open this intake folder.
  pause
  exit /b 1
)
call "%~dp0SETUP_RUNTIME_FOLDERS.bat"

echo Epistemic Intake v2 - three independent calls on today's tested OpenRouter route
echo Default test mode processes ONE file and moves it only after verified success.
echo.
python "%~dp0SCRIPTS\daily_api_preflight.py" --documents 1
if errorlevel 1 (
  echo Daily API gate failed. No file was processed.
  popd
  pause
  exit /b 1
)
call "%~dp0SCRIPTS\LOGS\daily-api-route.cmd"
python "%~dp0SCRIPTS\epistemic_intake_v2.py" --limit 1
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" echo One or more files failed. Failed originals remain in INBOX.
popd
pause
exit /b %EXIT_CODE%
