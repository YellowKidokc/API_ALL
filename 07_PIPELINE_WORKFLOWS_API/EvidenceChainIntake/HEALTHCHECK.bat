@echo off
setlocal
pushd "%~dp0" || (
  echo ERROR: Could not open the Evidence Chain Intake folder.
  pause
  exit /b 1
)
python -m py_compile "%~dp0SCRIPTS\run_packet.py" "%~dp0SCRIPTS\semantic_analysis.py" "%~dp0SCRIPTS\transfer_outbox.py" "%~dp0SCRIPTS\epistemic_intake_v2.py"
if errorlevel 1 (
  set "EXIT_CODE=%ERRORLEVEL%"
  popd
  pause
  exit /b %EXIT_CODE%
)
echo Evidence Chain Intake health check passed.
popd
pause
