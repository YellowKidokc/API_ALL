@echo off
setlocal
cd /d "%~dp0"
py -3 scripts\fruits_grade.py --config config.json --workers 2 --limit 2
if errorlevel 1 (
  echo.
  echo Pilot finished with an error. Review the run receipts in the output folder.
  pause
  exit /b 1
)
echo.
echo Two-paper Fruits pilot complete.
pause
