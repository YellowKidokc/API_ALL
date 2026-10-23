@echo off
setlocal
set "API_HOME=%~dp0"
where py >nul 2>nul && (py -3 "%API_HOME%engine\web.py" %* & exit /b %errorlevel%)
where python >nul 2>nul && (python "%API_HOME%engine\web.py" %* & exit /b %errorlevel%)
echo Python 3 was not found. Run INSTALL.bat first.
pause
exit /b 9009
