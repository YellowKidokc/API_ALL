@echo off
setlocal
rem Everything runs from the hidden _system folder next to this file.
set "SYS=%~dp0_system\"
if not defined DEEPSEEK_API_KEY echo DEEPSEEK_API_KEY is not set. Run SETUP.bat once (or add it under Windows environment variables). & echo.
where py >nul 2>nul && (py -3 "%SYS%engine\menu.py" %* & exit /b %errorlevel%)
where python >nul 2>nul && (python "%SYS%engine\menu.py" %* & exit /b %errorlevel%)
echo Python 3 was not found. Install it or add it to PATH.
pause
exit /b 9009
