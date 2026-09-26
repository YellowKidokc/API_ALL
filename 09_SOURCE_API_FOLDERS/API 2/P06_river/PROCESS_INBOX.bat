@echo off
echo Processing inbox for P06_river...
cd /d %~dp0
python _front_door\process_inbox.py
pause
