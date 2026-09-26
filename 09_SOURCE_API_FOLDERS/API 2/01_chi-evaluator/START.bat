@echo off
setlocal
cd /d "%~dp0"

echo.
echo ============================================================
echo   chi-Evaluator v2  --  Coherence Pressure Engine
echo   chi = G x M x E x S_eff x T x K x R x Q x F x C
echo ============================================================
echo.
echo   Drop .txt files (one claim per line) into INBOX\
echo   Results go to OUTBOX\run_TIMESTAMP\
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH.
    pause
    exit /b 1
)

echo   Installing dependencies...
python -m pip install openai openpyxl -q

echo.
python run_evaluator.py
if errorlevel 1 (
    echo.
    echo ERROR — see output above.
    pause
    exit /b 1
)

pause
