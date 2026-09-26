@echo off
echo Starting P04_paper_recommender preference engine...
cd /d %~dp0
python _front_door\health.py
echo.
echo P04 ready on port 20104
pause
