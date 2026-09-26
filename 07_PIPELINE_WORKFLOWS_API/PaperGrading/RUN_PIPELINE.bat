@echo off
setlocal
cd /d "%~dp0"
python SCRIPTS\run_packet.py --mode pipeline
set "PIPELINE_EXIT=%ERRORLEVEL%"
pause
exit /b %PIPELINE_EXIT%
