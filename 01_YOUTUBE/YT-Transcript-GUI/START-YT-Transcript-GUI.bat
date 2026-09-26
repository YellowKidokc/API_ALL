@echo off
setlocal EnableExtensions

set "ROOT=%~dp0"
set "SCRIPT=%ROOT%YT-Transcript.ahk"
set "TOOL=D:\GitHub\yt-bulk-subtitles-downloader\YTBSD_MENU.bat"

echo YouTube Transcript / Research GUI
echo =================================
echo.

if not exist "%SCRIPT%" (
  echo Missing script:
  echo %SCRIPT%
  pause
  exit /b 1
)

if not exist "%TOOL%" (
  echo Missing YT bulk subtitles downloader menu:
  echo %TOOL%
  echo.
  echo Run setup in D:\GitHub\yt-bulk-subtitles-downloader first.
  pause
  exit /b 1
)

call :find_ahk
if not "%AHK%"=="" goto launch

echo AutoHotkey was not found.
echo.
echo Trying to install AutoHotkey with winget...
where winget >nul 2>nul
if "%ERRORLEVEL%"=="0" (
  winget install AutoHotkey.AutoHotkey --silent --accept-source-agreements --accept-package-agreements
  call :find_ahk
)

if "%AHK%"=="" (
  echo.
  echo AutoHotkey still was not found.
  echo Install AutoHotkey from https://www.autohotkey.com/ then run this again.
  pause
  exit /b 1
)

:launch
echo Launching:
echo %SCRIPT%
echo.
echo Stopping any previous YT-Transcript watcher instance...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-CimInstance Win32_Process | Where-Object { $_.Name -like 'AutoHotkey*' -and $_.CommandLine -like '*YT-Transcript.ahk*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" >nul 2>nul
powershell -NoProfile -ExecutionPolicy Bypass -Command "$root = (Resolve-Path -LiteralPath '%ROOT%').Path; Start-Process -FilePath '%AHK%' -ArgumentList @('/ErrorStdOut', (Join-Path $root 'YT-Transcript.ahk')) -WorkingDirectory $root -WindowStyle Hidden"
exit /b 0

:find_ahk
set "AHK="
if exist "%ProgramFiles%\AutoHotkey\v1.1.37.02\AutoHotkeyU64.exe" (
  set "AHK=%ProgramFiles%\AutoHotkey\v1.1.37.02\AutoHotkeyU64.exe"
  exit /b 0
)
for %%P in (
  "%ProgramFiles%\AutoHotkey\v1.1.37.02\AutoHotkeyU64_UIA.exe"
  "%ProgramFiles%\AutoHotkey\AutoHotkey64.exe"
  "%LocalAppData%\Programs\AutoHotkey\v2\AutoHotkey64.exe"
  "%ProgramFiles%\AutoHotkey\v2\AutoHotkey64.exe"
  "%ProgramFiles%\AutoHotkey\v2\AutoHotkey.exe"
  "%ProgramFiles%\AutoHotkey\AutoHotkey.exe"
  "%LocalAppData%\Programs\AutoHotkey\v2\AutoHotkey.exe"
) do (
  if exist "%%~P" if %%~zP GTR 0 (
    set "AHK=%%~P"
    exit /b 0
  )
)
if "%AHK%"=="" (
  for %%E in (AutoHotkey64.exe AutoHotkey.exe AutoHotkeyU64.exe) do (
    where %%E >nul 2>nul
    if not errorlevel 1 for /f "delims=" %%A in ('where %%E') do if "%AHK%"=="" set "AHK=%%A"
  )
)
exit /b 0
