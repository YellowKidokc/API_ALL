@echo off
setlocal
rem Run once after copying or moving this folder. Safe to run again any time.
rem   1. DeepSeek key: kept in your Windows user environment variables, never in a file here
rem   2. paths: finds every data folder again after a move (_system\engine\relocate.py)
rem   3. hides _system and _data so this folder shows only ONE_MENU.bat and SETUP.bat
set "HERE=%~dp0"
set "SYS=%HERE%_system\"
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY (where python >nul 2>nul && set "PY=python")
if not defined PY (echo Python 3 was not found. Install it or add it to PATH. & pause & exit /b 9009)

echo 1  DeepSeek key
if defined DEEPSEEK_API_KEY (
  echo    DEEPSEEK_API_KEY is set.
) else (
  echo    DEEPSEEK_API_KEY is not set. Paste your key and press Enter ^(or just Enter to skip^).
  set /p "NEWKEY=   key: "
)
if defined NEWKEY (
  setx DEEPSEEK_API_KEY "%NEWKEY%" >nul && set "DEEPSEEK_API_KEY=%NEWKEY%"
  echo    Saved in your user environment variables. Windows opened before now will not see it: close them.
)
echo.

echo 2  Paths
%PY% "%SYS%engine\relocate.py" %*
echo.

echo 3  Hiding the machinery
if not exist "%HERE%_data" mkdir "%HERE%_data"
attrib +h "%SYS:~0,-1%" >nul 2>nul
attrib +h "%HERE%_data" >nul 2>nul
echo    _system and _data are hidden. Results: ONE_MENU.bat results
echo.
pause
