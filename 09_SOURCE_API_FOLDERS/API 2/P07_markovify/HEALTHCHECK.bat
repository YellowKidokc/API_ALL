@echo off
echo Running health check for P07_markovify...
cd /d %~dp0
python _front_door\health.py
pause
