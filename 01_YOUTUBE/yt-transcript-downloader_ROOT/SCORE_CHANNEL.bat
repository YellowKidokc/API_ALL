@echo off
REM Drag a CHANNEL/PLAYLIST folder (or the whole YOUTUBE folder) onto this file.
REM Re-running is safe: the scorecard block in each note is replaced, not duplicated.
cd /d "%~dp0"
if "%~1"=="" (
  python score_chapters.py "C:\Users\David\Documents\faiththruphysics.com\30_FRAMEWORKS\YOUTUBE"
) else (
  python score_chapters.py "%~1"
)
pause
