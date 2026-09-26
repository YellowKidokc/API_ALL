@echo off
echo Running health check for P01_implicit...
cd /d %~dp0
python _front_door\health.py
pause
