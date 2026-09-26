@echo off
:: ============================================================
::  PROCESS  —  Drop files in INBOX\ then double-click this
::  1. Vectorizes everything in INBOX\
::  2. Runs the 12 questions against the full corpus
::  3. Saves the analysis to OUTBOX\
::  4. Moves processed files from INBOX\ to OUTBOX\
:: ============================================================
title Writing Analyzer — Processing...
cd /d "%~dp0"

echo.
echo ============================================================
echo   Writing Analyzer
echo ============================================================
echo.

:: Check for files in INBOX
set INBOX_EMPTY=true
for %%f in ("%~dp0INBOX\*") do (
    if not "%%~nxf"==".gitkeep" set INBOX_EMPTY=false
)

if "%INBOX_EMPTY%"=="true" (
    echo   INBOX\ is empty.
    echo   Drop files into INBOX\ then run this script.
    echo.
    pause
    exit /b 0
)

echo   Step 1 of 3  —  Vectorizing INBOX files...
echo   --------------------------------------------
python "%~dp0vectorize.py" --source "%~dp0INBOX" --db "%~dp0vectorization"
if %errorlevel% neq 0 (
    echo.
    echo   ERROR during vectorization. See above.
    pause
    exit /b 1
)

echo.
echo   Step 2 of 3  —  Running analysis (calling DeepSeek)...
echo   -------------------------------------------------------
python "%~dp0process_runner.py"
if %errorlevel% neq 0 (
    echo.
    echo   ERROR during analysis. See above.
    pause
    exit /b 1
)

echo.
echo   Step 3 of 3  —  Moving files to OUTBOX...
echo   ------------------------------------------
python "%~dp0move_to_outbox.py"

echo.
echo ============================================================
echo   Done!  Check OUTBOX\ for your results.
echo ============================================================
echo.
pause
