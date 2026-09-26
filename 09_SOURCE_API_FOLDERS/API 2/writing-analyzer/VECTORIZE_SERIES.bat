@echo off
:: ============================================================
::  Vectorize New Series  —  Add any folder as a searchable corpus
::  Double-click, enter the series name and folder path, done.
:: ============================================================
title Vectorize New Series
cd /d "%~dp0"

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found.
    pause
    exit /b 1
)

python -c "import chromadb" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing chromadb ...
    pip install chromadb sentence-transformers beautifulsoup4
    echo.
)

python "%~dp0vectorize_series.py"
