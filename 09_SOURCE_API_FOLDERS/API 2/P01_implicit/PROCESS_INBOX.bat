@echo off
echo Processing inbox for P01_implicit...
cd /d %~dp0
python _front_door\process_inbox.py
pause
