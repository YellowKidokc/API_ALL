@echo off
echo Running health check for P02_recbole...
cd /d %~dp0
python _front_door\health.py
pause
