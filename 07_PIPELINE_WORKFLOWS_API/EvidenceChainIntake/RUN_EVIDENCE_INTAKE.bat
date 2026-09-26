@echo off
setlocal
pushd "%~dp0" || (
  echo ERROR: Could not open the Evidence Chain Intake folder.
  pause
  exit /b 1
)
python "%~dp0SCRIPTS\run_packet.py"
set "INTAKE_EXIT=%ERRORLEVEL%"
if not "%INTAKE_EXIT%"=="0" echo WARNING: Intake reported one or more errors. Continuing with valid records.
python "%~dp0SCRIPTS\semantic_analysis.py"
set "SEMANTIC_EXIT=%ERRORLEVEL%"
set "EXIT_CODE=0"
if not "%INTAKE_EXIT%"=="0" set "EXIT_CODE=1"
if not "%SEMANTIC_EXIT%"=="0" set "EXIT_CODE=1"
popd
pause
exit /b %EXIT_CODE%
