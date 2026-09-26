@echo off
setlocal
cd /d "%~dp0"

echo.
echo ============================================================
echo   EXCEL INTERROGATION
echo   Prompt 12 x Excel Data (direct) x DeepSeek + O3
echo ============================================================
echo.
echo   Reads the Excel workbook directly — no vectorization.
echo   Runs the three adversarial questions through both models.
echo.
echo   Results: universality-class-runner\excel_run_TIMESTAMP\
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found on PATH.
    pause
    exit /b 1
)

pip install openai pywin32 openpyxl -q

python run_excel_interrogation.py
if errorlevel 1 (
    echo.
    echo ERROR — see output above.
    pause
    exit /b 1
)

echo.
pause
