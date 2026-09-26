@echo off
echo Processing inbox for P02_recbole...
cd /d %~dp0
python _front_door\process_inbox.py
pause
