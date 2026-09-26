@echo off
cd /d "%~dp0"
REM own venv (the parent project's venv points at a removed Python install)
if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv venv
)
venv\Scripts\python.exe -m pip install -q -U yt-dlp
set PATH=%~dp0venv\Scripts;%PATH%
venv\Scripts\python.exe server.py
pause
