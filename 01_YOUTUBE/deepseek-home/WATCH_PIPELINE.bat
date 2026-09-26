@echo off
cd /d "%~dp0"
title DeepSeek Home - watching for new transcripts
REM Leave this window open. Every minute it converts new drops, cleans new transcripts,
REM and sends newly cleaned videos to DeepSeek. Close the window (or Ctrl+C) to stop.
python watch_pipeline.py %*
pause
