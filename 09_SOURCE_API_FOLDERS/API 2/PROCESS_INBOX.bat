@echo off
echo Processing inbox for 06_ENGINES...
cd /d X:\06_ENGINES
python _front_door\process_inbox.py 2>nul || echo No processor yet
pause
