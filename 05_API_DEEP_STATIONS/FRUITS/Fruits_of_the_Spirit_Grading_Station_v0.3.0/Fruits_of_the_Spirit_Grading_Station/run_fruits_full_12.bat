@echo off
setlocal
cd /d "%~dp0"
py -3 scripts\fruits_grade.py --config config.json --workers 12 --limit 0
if errorlevel 1 (
  echo.
  echo Batch finished with one or more errors. Review _batch_summary.json and the run receipts.
  pause
  exit /b 1
)
echo.
echo Fruits batch complete.
pause
