@echo off
setlocal EnableDelayedExpansion
pushd "%~dp0" || (
  echo ERROR: Could not open EVIDENCE folder.
  pause
  exit /b 1
)

echo =========================================================================
echo  PAIR GOD IS UNPROVEN CLAIMS WITH LEAN 4 FORMALIZATION ENGINE
echo =========================================================================
echo.

python -u "%~dp0SCRIPTS\god_is_unproven_to_lean.py" %*
set "EXIT_CODE=%ERRORLEVEL%"

echo.
echo Pairing finished with status code: %EXIT_CODE%
echo Master Matrix: EVIDENCE\OUTBOX\GOD_IS_UNPROVEN_CLAIMS_LEAN_PAIRING.md
echo.

popd
pause
exit /b %EXIT_CODE%
