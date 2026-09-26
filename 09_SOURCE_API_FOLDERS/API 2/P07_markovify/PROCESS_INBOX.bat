@echo off
echo Processing inbox for P07_markovify...
cd /d %~dp0
python _front_door\process_inbox.py
pause
