@echo off
setlocal EnableExtensions
cd /d "%~dp0"

:menu
cls
echo ============================================================
echo YouTube Bulk Subtitles Downloader - Menu
echo ============================================================
echo.
echo Project: %CD%
echo.
echo  1. Start downloader
echo  2. Install / repair dependencies
echo  3. Troubleshoot / health check
echo  4. Update Python packages
echo  5. Open subtitles output folder
echo  6. Open project folder
echo  7. Show quick help
echo  0. Exit
echo.
set /p choice=Choose an option: 

if "%choice%"=="1" goto start
if "%choice%"=="2" goto setup
if "%choice%"=="3" goto troubleshoot
if "%choice%"=="4" goto update
if "%choice%"=="5" goto open_subtitles
if "%choice%"=="6" goto open_project
if "%choice%"=="7" goto help
if "%choice%"=="0" goto done
goto menu

:start
call "%~dp0START_YTBSD.bat"
pause
goto menu

:setup
call "%~dp0setup.bat"
pause
goto menu

:troubleshoot
call "%~dp0TROUBLESHOOT_YTBSD.bat"
pause
goto menu

:update
if not exist "%~dp0venv\Scripts\python.exe" (
  echo Virtual environment not found. Running setup first...
  call "%~dp0setup.bat"
)
echo.
echo Updating packages from requirements.txt...
"%~dp0venv\Scripts\python.exe" -m pip install --upgrade pip
"%~dp0venv\Scripts\python.exe" -m pip install --upgrade -r "%~dp0requirements.txt"
echo.
echo Update complete.
pause
goto menu

:open_subtitles
if not exist "%~dp0subtitles" mkdir "%~dp0subtitles"
start "" "%~dp0subtitles"
goto menu

:open_project
start "" "%~dp0"
goto menu

:help
cls
echo ============================================================
echo Quick Help
echo ============================================================
echo.
echo What this tool does:
echo   Downloads available YouTube captions/subtitles from a video,
echo   playlist, or channel, then saves them under the subtitles folder.
echo.
echo Normal path:
echo   1. Run option 2 once if dependencies are missing.
echo   2. Run option 1 to start.
echo   3. Paste a YouTube video, playlist, or channel URL when asked.
echo.
echo Requirements:
echo   - Python 3.8 or newer
echo   - Google Chrome, used by Selenium when fetching fresh proxies
echo   - Internet access
echo.
echo If something fails:
echo   Run option 3. It writes a timestamped log to the logs folder.
echo.
pause
goto menu

:done
endlocal
