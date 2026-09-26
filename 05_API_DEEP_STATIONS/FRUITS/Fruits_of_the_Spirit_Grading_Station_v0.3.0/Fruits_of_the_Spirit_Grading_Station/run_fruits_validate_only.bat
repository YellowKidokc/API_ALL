@echo off
setlocal
cd /d "%~dp0"
py -3 scripts\fruits_grade.py --config config.json --validate-only
if errorlevel 1 (
  echo.
  echo Validation failed. Review the messages above.
  pause
  exit /b 1
)
echo.
echo Validation passed.
pause
