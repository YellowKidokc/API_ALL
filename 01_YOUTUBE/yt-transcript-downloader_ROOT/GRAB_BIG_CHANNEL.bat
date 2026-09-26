@echo off
REM Big-channel download: fetch in batches, resume forever, never lose work.
REM Every transcript is written the moment it is captured, so closing this
REM window or losing power costs at most the video in flight.
REM   GRAB_BIG_CHANNEL.bat "https://www.youtube.com/@gracetoyou" "E:\YouTube\channels\MacArthur"
setlocal enabledelayedexpansion
set "CHUNK=250"
set "MAX_SESSIONS=20"
set "PAUSE_SECONDS=90"
set "URL=%~1"
set "OUT=%~2"
if "%URL%"=="" goto :usage
if "%OUT%"=="" goto :usage

set "PY=%~dp0venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

echo ============================================================
echo   Big channel download
echo   Folder: %OUT%
echo   %CHUNK% videos per batch, up to %MAX_SESSIONS% batches this sitting.
echo   Safe to close at any time - finished videos are already saved.
echo ============================================================
echo.
"%PY%" "%~dp0ytgrab.py" "%URL%" --out "%OUT%" --status

for /l %%S in (1,1,%MAX_SESSIONS%) do (
  echo.
  echo ------------------------- batch %%S of %MAX_SESSIONS% -------------------------
  "%PY%" "%~dp0ytgrab.py" "%URL%" --out "%OUT%" --limit %CHUNK% --free-proxies
  call :remaining
  if "!REMAIN!"=="0" goto :done
  echo.
  echo !REMAIN! still to fetch. Pausing %PAUSE_SECONDS%s to let the rate limit cool...
  timeout /t %PAUSE_SECONDS% /nobreak >nul
)

:done
echo.
echo ============================================================
"%PY%" "%~dp0ytgrab.py" "%URL%" --out "%OUT%" --status
echo.
echo Run this again whenever you want to continue.
echo ============================================================
pause
exit /b 0

:remaining
set "REMAIN=?"
"%PY%" "%~dp0ytgrab.py" "%URL%" --out "%OUT%" --status > "%TEMP%\ytstatus.txt" 2>nul
for /f "usebackq tokens=4" %%R in (`findstr /c:"still to fetch:" "%TEMP%\ytstatus.txt"`) do set "REMAIN=%%R"
exit /b 0

:usage
echo Usage: GRAB_BIG_CHANNEL.bat "channel-url" "output-folder"
pause
exit /b 1
