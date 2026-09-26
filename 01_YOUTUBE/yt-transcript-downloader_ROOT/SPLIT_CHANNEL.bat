@echo off
REM Drag a combined channel_*.md or playlist_*.md onto this file.
cd /d "%~dp0"
if "%~1"=="" (
  echo Drag a combined channel or playlist .md file onto SPLIT_CHANNEL.bat
  pause
  exit /b 1
)
python split_channel_chapters.py "%~1" %2 %3 %4
pause
