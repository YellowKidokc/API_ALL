@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo Starting YouTube Bulk Subtitles Downloader
echo ============================================================
echo.

if not exist "%~dp0venv\Scripts\python.exe" (
  echo The virtual environment is missing.
  echo.
  set /p setup_now=Run setup now? [Y/N]: 
  if /i "%setup_now%"=="Y" (
    call "%~dp0setup.bat"
  ) else (
    echo Start cancelled. Run setup.bat or YTBSD_MENU.bat option 2 first.
    exit /b 1
  )
)

if not exist "%~dp0ytbsd.py" (
  echo ERROR: ytbsd.py was not found in:
  echo   %~dp0
  exit /b 1
)

call "%~dp0venv\Scripts\activate.bat"
python "%~dp0ytbsd.py"
set "EXIT_CODE=%ERRORLEVEL%"

echo.
echo ============================================================
if "%EXIT_CODE%"=="0" (
  echo Downloader closed normally.
) else (
  echo Downloader stopped with error code %EXIT_CODE%.
  echo Run TROUBLESHOOT_YTBSD.bat or YTBSD_MENU.bat option 3.
)
echo ============================================================
exit /b %EXIT_CODE%
