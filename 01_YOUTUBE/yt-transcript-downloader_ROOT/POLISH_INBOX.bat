@echo off
cd /d "%~dp0"
if exist venv\Scripts\python.exe (
    venv\Scripts\python.exe transcript_polish.py
) else (
    python transcript_polish.py
)
pause
