@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0RUN_WITH_WEBSHARE.ps1"
set "RESULT=%ERRORLEVEL%"
echo.
echo Downloader finished with status %RESULT%.
pause
exit /b %RESULT%
