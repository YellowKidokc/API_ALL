@echo off
echo Processing inbox for P05_ppk...
cd /d %~dp0
python _front_door\process_inbox.py
pause
