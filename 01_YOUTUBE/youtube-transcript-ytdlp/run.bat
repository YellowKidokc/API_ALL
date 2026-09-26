@echo off
echo ============================================================
echo YouTube Transcript Scraper (yt-dlp method)
echo ============================================================
echo.

REM Check if venv exists
if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
    echo Installing dependencies...
    venv\Scripts\pip.exe install -r requirements.txt
    echo.
)

echo Starting scraper...
echo.
venv\Scripts\python.exe scraper.py

echo.
echo ============================================================
echo Done!
echo ============================================================
pause
