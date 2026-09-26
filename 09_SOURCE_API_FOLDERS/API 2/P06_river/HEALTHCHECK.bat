@echo off
echo Running health check for P06_river...
cd /d %~dp0
python _front_door\health.py
pause
