@echo off
setlocal
cd /d "%~dp0"

echo.
echo ============================================================
echo   PASS 2  --  Extract discoveries from last run, then
echo              re-run ONE / TWO / THREE with enriched context
echo ============================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found.
    pause
    exit /b 1
)

pip install openai chromadb sentence-transformers -q

echo.
echo   Step 1 of 2: Extracting discoveries from last run...
echo.
python extract_discoveries.py
if errorlevel 1 (
    echo.
    echo ERROR in extract_discoveries.py — see above.
    pause
    exit /b 1
)

echo.
echo   Step 2 of 2: Re-running prompts with enriched context...
echo.
python run_pass2.py
if errorlevel 1 (
    echo.
    echo ERROR in run_pass2.py — see above.
    pause
    exit /b 1
)

echo.
echo   To run another iteration: double-click PASS2.bat again.
echo   Stop when two consecutive passes produce no new findings.
echo.
pause
