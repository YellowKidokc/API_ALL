@echo off
echo Processing inbox for P04_paper_recommender...
cd /d %~dp0
python _front_door\process_inbox.py
pause
