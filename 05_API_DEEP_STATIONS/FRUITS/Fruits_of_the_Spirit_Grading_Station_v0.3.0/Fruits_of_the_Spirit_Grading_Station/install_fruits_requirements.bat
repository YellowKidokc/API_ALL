@echo off
setlocal
cd /d "%~dp0"
py -3 -m pip install --user -r requirements.txt
if errorlevel 1 (
  echo.
  echo Installation failed. Confirm that Python 3 and internet access are available.
  pause
  exit /b 1
)
echo.
echo Fruits station document readers installed.
pause
