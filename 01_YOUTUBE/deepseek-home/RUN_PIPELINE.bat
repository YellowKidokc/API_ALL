@echo off
setlocal
cd /d "%~dp0"
title DeepSeek Home - YouTube pipeline

REM Safe to run any time, even while downloads are still coming in.
REM Finished work is skipped; transcripts written in the last 2 minutes wait for the next run.
REM Usage: RUN_PIPELINE.bat [channel folder name]   (no name = every channel)

set "ROOT=%~dp0..\.."
for %%I in ("%ROOT%") do set "ROOT=%%~fI"
set "SUBS=%ROOT%\subtitles"
set "VENV=%ROOT%\venv\Scripts\python.exe"
set "CHAN=%~1"

echo === 0/4  Conversion station: SRT/VTT/JSON/pasted transcripts -^> subtitles\^<Channel^> ===
if exist "X:\00_CONVERSION_STATION\Transcripts to Markdown\scripts\Run-Inbox.ps1" (
  powershell -NoProfile -ExecutionPolicy Bypass -File "X:\00_CONVERSION_STATION\Transcripts to Markdown\scripts\Run-Inbox.ps1"
) else (
  echo   conversion station not reachable on X: - skipping
)

echo === 1/4  Clean new transcripts (local Python, no API) ===
pushd "%ROOT%\Python Clean Library"
if defined CHAN (
  "%VENV%" clean_library.py --src "%SUBS%" --out "%ROOT%\obsidian_transcripts" --channel "%CHAN%" --punctuate
) else (
  "%VENV%" clean_library.py --src "%SUBS%" --out "%ROOT%\obsidian_transcripts" --punctuate
)
popd

echo === 2/4  Index new or changed transcripts (DeepSeek; channels in WATCH_CHANNELS.txt only) ===
if defined CHAN (
  python index_video.py "%SUBS%\%CHAN%" --workers 8
) else (
  for /f "usebackq eol=# delims=" %%C in ("WATCH_CHANNELS.txt") do python index_video.py "%SUBS%\%%C" --workers 8
)

echo === 3/4  Redraw notes with any newly cleaned transcripts (no API) ===
if defined CHAN (
  python index_video.py "%SUBS%\%CHAN%" --render-only >nul
) else (
  for /f "usebackq eol=# delims=" %%C in ("WATCH_CHANNELS.txt") do python index_video.py "%SUBS%\%%C" --render-only >nul
)

echo === 4/4  Rebuild catalog, channel overviews and debate pages ===
python build_catalog.py

echo.
echo Done. Notes: %ROOT%\obsidian_indexed
pause
