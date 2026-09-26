@echo off
setlocal
cd /d "%~dp0"
title Python Clean Library

REM ------------------------------------------------------------------
REM  Where things live. By default: the folder this .bat sits in is
REM  inside yt-transcript-downloader, next to subtitles\.
REM  Change these three lines to point it somewhere else.
REM ------------------------------------------------------------------
set "SUBS=%~dp0..\subtitles"
set "NOTES=%~dp0..\obsidian_transcripts"
set "ZIPS=%~dp0..\_archive_zips"
for %%I in ("%SUBS%") do set "SUBS=%%~fI"
for %%I in ("%NOTES%") do set "NOTES=%%~fI"
for %%I in ("%ZIPS%") do set "ZIPS=%%~fI"

REM Pick a Python: the downloader's venv if present, otherwise system Python.
set "PY=python"
if exist "%~dp0..\venv\Scripts\python.exe" set "PY=%~dp0..\venv\Scripts\python.exe"

REM Use the local punctuation model only if it has been installed.
set "PUNCT="
"%PY%" -c "import punctuators" >nul 2>&1 && set "PUNCT=--punctuate"

echo ==================================================================
echo  Step 1 of 2 - Sort loose transcripts into channel folders
echo ==================================================================
"%PY%" sort_by_channel.py --dir "%SUBS%" --apply
if errorlevel 1 goto :failed

echo.
echo ==================================================================
echo  Step 2 of 2 - Clean new/changed transcripts into Obsidian notes
if defined PUNCT (echo  ^(punctuation model: ON^)) else (echo  ^(punctuation model: not installed - basic clean only^))
echo ==================================================================
"%PY%" clean_library.py --src "%SUBS%" --out "%NOTES%" %PUNCT%
if errorlevel 1 goto :failed

echo.
echo Done. Notes are in: %NOTES%
echo.
set /p ZIPIT="Zip the ORIGINAL transcripts of fully cleaned channels now? (y/N) "
if /i "%ZIPIT%"=="y" "%PY%" clean_library.py --src "%SUBS%" --out "%NOTES%" --archive --zips "%ZIPS%"
if /i "%ZIPIT%"=="y" echo Zips are in: %ZIPS%   (originals were NOT deleted)
echo.
pause
exit /b 0

:failed
echo.
echo Something went wrong - see the messages above.
pause
exit /b 1
