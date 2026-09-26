@echo off
echo Starting P03_lightfm preference engine...
cd /d %~dp0
python _front_door\health.py
echo.
echo P03 ready on port 20103
pause
