@echo off
setlocal
set "API_HOME=%~dp0"
where py >nul 2>nul && (py -3 "%API_HOME%engine\relocate.py" %* & exit /b %errorlevel%)
python "%API_HOME%engine\relocate.py" %*
