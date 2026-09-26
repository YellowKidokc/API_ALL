@echo off
echo Starting P07_markovify preference engine...
cd /d %~dp0
python _front_door\health.py
echo.
echo P07 ready on port 20107
pause
