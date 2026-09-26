@echo off
setlocal
title Grab One YouTube Transcript - Free Direct Mode

echo.
echo Paste one YouTube video URL, then press Enter.
echo This uses the direct connection only. No paid proxy is used.
echo.
set /p "VIDEO_URL=YouTube URL: "

if not defined VIDEO_URL (
  echo.
  echo No URL was entered.
  pause
  exit /b 1
)

echo.
"%~dp0venv\Scripts\python.exe" "%~dp0ytgrab.py" "%VIDEO_URL%" --no-webshare
set "GRAB_EXIT=%ERRORLEVEL%"

echo.
if not "%GRAB_EXIT%"=="0" echo The grab did not complete successfully.
pause
exit /b %GRAB_EXIT%
