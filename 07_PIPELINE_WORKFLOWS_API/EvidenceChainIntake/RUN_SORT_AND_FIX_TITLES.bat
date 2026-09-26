@echo off
setlocal
pushd "%~dp0" || (
  echo ERROR: Could not open the Evidence Chain Intake folder.
  pause
  exit /b 1
)

echo =========================================================================
echo  EVIDENCE CHAIN INTAKE - GENTLE REREAD, TITLE POLISHING, AND DEEP SORTING
echo =========================================================================
echo.
echo 1. Preserves original folder structure in: OUTBOX\00_ORIGINAL_STRUCTURE\
echo 2. Organizes and cross-references copies into: OUTBOX\01_CATEGORIZED_DOMAINS\
echo 3. Emits audit receipts in: SCRIPTS\LOGS\
echo.

python "%~dp0SCRIPTS\organize_and_retake_folders.py"
set "EXIT_CODE=%ERRORLEVEL%"

popd
pause
exit /b %EXIT_CODE%
