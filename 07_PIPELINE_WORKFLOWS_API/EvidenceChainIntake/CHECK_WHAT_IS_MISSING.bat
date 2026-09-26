@echo off
setlocal
pushd "%~dp0" || exit /b 1
python "%~dp0SCRIPTS\check_epistemic_completion.py"
set "RESULT=%ERRORLEVEL%"
popd
pause
exit /b %RESULT%
