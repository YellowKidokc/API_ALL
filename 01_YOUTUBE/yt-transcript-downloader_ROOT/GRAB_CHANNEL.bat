@echo off
REM Route a YouTube download by size: small channels run once, big channels
REM run in resumable batches across as many sittings as they need.
REM   GRAB_CHANNEL.bat "https://www.youtube.com/@gracetoyou"
REM   GRAB_CHANNEL.bat "url" "E:\YouTube\channels\MacArthur"
REM Set DRYRUN=1 to see the plan without downloading.
setlocal
set "THRESHOLD=200"
set "URL=%~1"
if "%URL%"=="" goto :usage

set "PY=%~dp0venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

echo Counting videos on the channel...
"%PY%" "%~dp0channel_size.py" "%URL%" > "%TEMP%\ytcount.txt" 2>nul
set "COUNT=0"
set "NAME="
for /f "usebackq tokens=1,2 delims=|" %%A in ("%TEMP%\ytcount.txt") do (
  set "COUNT=%%A"
  set "NAME=%%B"
)

if "%COUNT%"=="0" (
  echo.
  echo Could not count this channel: %NAME%
  echo Check the URL, or pass a /videos or playlist URL directly.
  pause
  exit /b 1
)

set "OUT=%~2"
if "%OUT%"=="" set "OUT=E:\YouTube\channels\%NAME%"

echo.
echo   Channel: %NAME%
echo   Videos:  %COUNT%
echo   Folder:  %OUT%
echo.

if %COUNT% GEQ %THRESHOLD% (
  echo %COUNT% videos is over the %THRESHOLD% threshold - using the big-channel path.
  echo It downloads in resumable batches; close the window whenever you like.
  echo.
  if defined DRYRUN (
    echo [DRYRUN] would run: GRAB_BIG_CHANNEL.bat "%URL%" "%OUT%"
    pause
    exit /b 0
  )
  call "%~dp0GRAB_BIG_CHANNEL.bat" "%URL%" "%OUT%"
  exit /b %ERRORLEVEL%
)

echo %COUNT% videos - small enough for a single run.
echo.
if defined DRYRUN (
  echo [DRYRUN] would run: ytgrab.py "%URL%" --out "%OUT%" --free-proxies
  pause
  exit /b 0
)
"%PY%" "%~dp0ytgrab.py" "%URL%" --out "%OUT%" --free-proxies
echo.
pause
exit /b %ERRORLEVEL%

:usage
echo Usage: GRAB_CHANNEL.bat "channel-or-playlist-url" ["output-folder"]
echo.
echo Under %THRESHOLD% videos: one run.
echo Over %THRESHOLD%:  batched, resumable, multi-session.
pause
exit /b 1
