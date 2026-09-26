@echo off
echo Starting P02_recbole preference engine...
cd /d %~dp0
python _front_door\health.py
echo.
echo P02 ready on port 20102
pause
