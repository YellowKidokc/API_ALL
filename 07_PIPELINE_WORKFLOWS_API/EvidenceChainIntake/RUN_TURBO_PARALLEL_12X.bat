@echo off
setlocal
pushd "%~dp0" || (
  echo ERROR: Could not open this intake folder.
  pause
  exit /b 1
)
call "%~dp0SETUP_RUNTIME_FOLDERS.bat"

echo =========================================================================
echo  EPISTEMIC INTAKE V2 - ADAPTIVE TURBO ENGINE (12 OR 24 WORKERS)
echo =========================================================================
echo.
echo 1. Reads eligible papers in INBOX
echo 2. Uses 12 quality workers or 24 speed workers on a tested free route
echo    while pacing request starts to avoid the free-route rate limit
echo 3. Moves originals to PROCESSED_ORIGINALS only after cryptographic validation
echo 4. Outputs full epistemic cards into OUTBOX\04_EPISTEMIC_INTAKE_V2\
echo.

python "%~dp0SCRIPTS\daily_api_preflight.py"
if errorlevel 1 (
  echo.
  echo ERROR: Daily workload and free-model gate failed. No papers were processed.
  popd
  pause
  exit /b 1
)
call "%~dp0SCRIPTS\LOGS\daily-api-route.cmd"

python "%~dp0SCRIPTS\epistemic_intake_v2.py" --check
if errorlevel 1 (
  echo.
  echo ERROR: OpenRouter preflight failed. No papers were processed.
  popd
  pause
  exit /b 1
)

python "%~dp0SCRIPTS\epistemic_intake_v2.py" --all --limit %DAILY_API_MAX_FILES% --workers %DAILY_API_WORKERS%
set "EXIT_CODE=%ERRORLEVEL%"

echo.
echo Process completed with status code: %EXIT_CODE%
echo Each successful paper was titled, moved, routed, and receipted before completion.
echo.

if not "%EXIT_CODE%"=="0" echo One or more files encountered issues. Check SCRIPTS\LOGS\ for details.
popd
pause
exit /b %EXIT_CODE%
