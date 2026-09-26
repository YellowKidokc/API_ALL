@echo off
:: ============================================================
::  Vectorize  —  Ingest input\ files into ChromaDB
::  Double-click this to embed your files for RAG search
:: ============================================================
title Vectorize — ChromaDB Ingestion
cd /d "%~dp0"

echo.
echo ============================================================
echo   Vectorize  —  ChromaDB Ingestion
echo ============================================================
echo.
echo   Drop any text files into the input\ folder, then
echo   run this script to chunk and embed them.
echo.
echo   After vectorizing, set USE_VECTORDB=true in config.txt
echo   and run RUN.bat — DeepSeek will use your files as context.
echo.
echo ============================================================
echo.

:: Check Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Download it from https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Install chromadb if missing
python -c "import chromadb" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing chromadb ...
    pip install chromadb
    echo.
)

:: Install sentence-transformers if missing (needed for default embeddings)
python -c "import sentence_transformers" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing sentence-transformers ...
    pip install sentence-transformers
    echo.
)

:: Run vectorizer
python "%~dp0vectorize.py" %*

echo.
echo ============================================================
echo   To clear and re-ingest from scratch, run:
echo     VECTORIZE.bat --clear
echo ============================================================
pause
