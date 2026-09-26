@echo off
setlocal
cd /d "%~dp0"

echo.
echo ============================================================
echo   PROCESS MULTI  --  5 Prompts x Multi-Corpus
echo ============================================================
echo.
echo   Runs every prompt in prompts\ against all configured
echo   corpora (MDA + GTQ + Cannon), with the foundation
echo   document prepended to every call.
echo.
echo   Results saved to OUTBOX\run_TIMESTAMP\
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found on PATH.
    pause
    exit /b 1
)

pip install openai chromadb sentence-transformers beautifulsoup4 -q

echo   Installing / checking dependencies done.
echo.

python process_multi.py
if errorlevel 1 (
    echo.
    echo ERROR: process_multi.py failed — see output above.
    pause
    exit /b 1
)

echo.
pause
