@echo off
setlocal
cd /d "%~dp0"

echo.
echo ============================================================
echo   RUN THREE  --  ONE / TWO / THREE vs OpenAI O3 + DeepSeek
echo ============================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found.
    pause
    exit /b 1
)

pip install openai chromadb sentence-transformers -q

python run_three.py
if errorlevel 1 (
    echo.
    echo ERROR — see output above.
    pause
    exit /b 1
)

echo.
pause
