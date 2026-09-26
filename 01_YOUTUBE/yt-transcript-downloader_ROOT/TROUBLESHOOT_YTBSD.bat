@echo off
setlocal EnableExtensions
cd /d "%~dp0"

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0TROUBLESHOOT_YTBSD.ps1"
set "EXIT_CODE=%ERRORLEVEL%"

echo.
echo Troubleshooter exited with code %EXIT_CODE%.
endlocal
exit /b %EXIT_CODE%
