@echo off
setlocal
pushd "%~dp0" || (
  echo ERROR: Could not open the Evidence Chain Intake folder.
  pause
  exit /b 1
)
python "%~dp0SCRIPTS\transfer_outbox.py"
set "EXIT_CODE=%ERRORLEVEL%"
popd
pause
exit /b %EXIT_CODE%
