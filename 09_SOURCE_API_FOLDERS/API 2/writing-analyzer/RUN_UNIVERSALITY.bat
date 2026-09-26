@echo off
setlocal
cd /d "%~dp0"

echo.
echo ============================================================
echo   UNIVERSALITY CLASS TEST
echo   Prompt 11 x MDA + GTQ x DeepSeek + O3
echo ============================================================
echo.
echo   Tests whether domains in the corpus are independent
echo   MODEL INSTANCES of the same formal THEORY T — the
echo   correct mathematical classification (not isomorphism).
echo.
echo   Results saved to: universality-class-runner\run_TIMESTAMP\
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found on PATH.
    pause
    exit /b 1
)

pip install openai chromadb sentence-transformers beautifulsoup4 -q

python run_universality.py
if errorlevel 1 (
    echo.
    echo ERROR: run_universality.py failed — see output above.
    pause
    exit /b 1
)

echo.
echo Done. Check universality-class-runner\ for results.
echo.
pause
