@echo off
setlocal
pushd "%~dp0" || exit /b 1
call "%~dp0SETUP_RUNTIME_FOLDERS.bat"
echo ================================================================
echo  DAILY API GATE - WORKLOAD, FREE MODEL DISCOVERY, AND QUICK TESTS
echo ================================================================
echo.
python "%~dp0SCRIPTS\daily_api_preflight.py"
set "EXIT_CODE=%ERRORLEVEL%"
echo.
if not "%EXIT_CODE%"=="0" echo No production API work was authorized.
popd
pause
exit /b %EXIT_CODE%
