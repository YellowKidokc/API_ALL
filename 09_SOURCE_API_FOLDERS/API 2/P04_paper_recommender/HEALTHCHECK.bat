@echo off
echo Running health check for P04_paper_recommender...
cd /d %~dp0
python _front_door\health.py
pause
