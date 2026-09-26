@echo off
echo Processing inbox for P03_lightfm...
cd /d %~dp0
python _front_door\process_inbox.py
pause
