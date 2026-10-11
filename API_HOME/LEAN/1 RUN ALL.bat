@echo off
setlocal
rem Every Lean source in INBOX: priority, then series, then group. Finished ones are skipped.
set "SYS=%~dp0..\_system\"
if not defined DEEPSEEK_API_KEY echo DEEPSEEK_API_KEY is not set. Run SETUP.bat once. & pause & exit /b 1
where py >nul 2>nul && (py -3 "%SYS%engine\menu.py" 55 --yes  %* & goto :done)
python "%SYS%engine\menu.py" 55 --yes  %*
:done
echo.
echo Papers are in %~dp0OUTBOX
pause
