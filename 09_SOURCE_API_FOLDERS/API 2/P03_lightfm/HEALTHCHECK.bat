@echo off
echo Running health check for P03_lightfm...
cd /d %~dp0
python _front_door\health.py
pause
