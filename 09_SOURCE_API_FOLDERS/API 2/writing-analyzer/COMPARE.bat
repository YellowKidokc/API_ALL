@echo off
setlocal
cd /d "%~dp0"

echo.
echo ============================================================
echo   COMPARE  --  DeepSeek vs OpenAI O3
echo   Runs all prompts through both models side by side
echo ============================================================
echo.
echo   Paste your OpenAI key into config.txt (OPENAI_API_KEY=)
echo   before running if you have not already done so.
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found.
    pause
    exit /b 1
)

pip install openai chromadb sentence-transformers beautifulsoup4 -q

python process_compare.py
if errorlevel 1 (
    echo.
    echo ERROR — see output above.
    pause
    exit /b 1
)

echo.
pause
