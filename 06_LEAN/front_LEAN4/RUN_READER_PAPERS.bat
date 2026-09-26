@echo off
REM ==================================================================
REM  LEAN4 station - everyday-language reader papers for the curated corpus
REM  Uses the One Page Paper LEAN4 pipeline, but only for the files in
REM  READER_QUEUE_SHA256.txt (distinct files from ALL_LEAN4, Mathlib copies
REM  removed), in priority order: live-core axiom files, other axiom files,
REM  then everything else. Finished papers are skipped, so re-running is free.
REM  Papers + master list: One page paper API\LEAN4\OUTBOX\00_READ_PAPERS
REM ==================================================================
setlocal
pushd "%~dp0"
chcp 65001 >nul
set "PYTHONIOENCODING=utf-8"
title LEAN4 - Reader papers (curated queue)

set "PIPE=\\192.168.2.50\h_hp\Desktop\___Pipeline_Done_New\One page paper API\LEAN4\SCRIPTS\pipeline.py"
set "LEAN4_EXTRA_SCAN=\\192.168.2.50\h_hp\Desktop\ALL_LEAN4"
set "LEAN4_ONLY_SHA256_FILE=%~dp0READER_QUEUE_SHA256.txt"

set "WORKERS=%~1"
if "%WORKERS%"=="" set "WORKERS=30"

python -u "%PIPE%" deepseek --reader-papers --auto --workers %WORKERS%
set "RESULT=%ERRORLEVEL%"
echo.
echo Finished with exit code %RESULT%. Completed papers are saved; run again to continue.
pause
exit /b %RESULT%
