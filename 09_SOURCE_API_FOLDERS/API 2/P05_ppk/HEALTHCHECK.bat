@echo off
echo Running health check for P05_ppk...
cd /d %~dp0
python _front_door\health.py
pause
