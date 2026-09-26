@echo off
echo Health check 06_ENGINES...
cd /d X:\06_ENGINES
python _front_door\health.py 2>nul || echo No health script yet
pause
