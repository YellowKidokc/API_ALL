@echo off
setlocal EnableDelayedExpansion
pushd "%~dp0" || (
  echo ERROR: Could not open EVIDENCE folder.
  pause
  exit /b 1
)

echo =========================================================================
echo  FAITH THROUGH PHYSICS - SYNC PIPELINE TO SQLITE (D: DRIVE)
echo =========================================================================
echo.

python -u "%~dp0SCRIPTS\sync_to_sqlite.py" %*
set "EXIT_CODE=%ERRORLEVEL%"

echo.
echo Sync completed with status code: %EXIT_CODE%
echo Target DB: D:\GitHub\Canonizationv1\theophysics_pipeline.db
echo.

popd
pause
exit /b %EXIT_CODE%
