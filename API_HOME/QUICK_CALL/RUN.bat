@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul && (py -3 call.py  %* & goto :done)
python call.py  %*
:done
pause
