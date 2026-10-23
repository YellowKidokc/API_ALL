@echo off
setlocal EnableDelayedExpansion
title ONE_MENU installer
set "API_HOME=%~dp0"
echo ==================================================
echo   ONE_MENU installer
echo ==================================================
echo.

rem ---- 1. Python ------------------------------------------------
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY (
  echo [1/5] Python not found. Installing Python 3.12 with winget...
  where winget >nul 2>nul || (
    echo winget is not available. Install Python from https://www.python.org/downloads/
    echo and tick "Add python.exe to PATH", then run INSTALL.bat again.
    start "" https://www.python.org/downloads/
    pause & exit /b 1
  )
  winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
  echo.
  echo Python installed. Close this window and double-click INSTALL.bat again.
  pause & exit /b 0
)
echo [1/5] Python found:
%PY% --version

rem ---- 2. Packages ----------------------------------------------
echo.
echo [2/5] Installing Python packages...
%PY% -m pip install --upgrade pip
%PY% -m pip install -r "%API_HOME%requirements.txt"
if errorlevel 1 echo WARNING: some packages failed. ONE_MENU still runs; Excel and legacy stations may not.

rem ---- 3. API keys ----------------------------------------------
echo.
echo [3/5] API keys (stored in your Windows user environment, never in files)
if defined DEEPSEEK_API_KEY (echo DEEPSEEK_API_KEY already set.) else (
  set "K="
  set /p "K=Paste DeepSeek API key (Enter to skip): "
  if defined K setx DEEPSEEK_API_KEY "!K!" >nul && set "DEEPSEEK_API_KEY=!K!" && echo Saved.
)
if defined OPENAI_API_KEY (echo OPENAI_API_KEY already set.) else (
  set "K="
  set /p "K=Paste OpenAI API key (Enter to skip): "
  if defined K setx OPENAI_API_KEY "!K!" >nul && set "OPENAI_API_KEY=!K!" && echo Saved.
)

rem ---- 4. Folder locations --------------------------------------
echo.
echo [4/5] Folder locations. For each MISSING entry paste the folder path,
echo       or press Enter to skip it for now (rerun RELOCATE.bat any time).
%PY% "%API_HOME%engine\relocate.py"

rem ---- 5. Shortcuts (Start Menu + Desktop, no console window) ---
echo.
echo [5/5] Installing ONE_MENU into your Start Menu and Desktop...
for /f "delims=" %%P in ('%PY% -c "import sys,os;print(os.path.join(os.path.dirname(sys.executable),'pythonw.exe'))"') do set "PYW=%%P"
if not exist "%PYW%" for /f "delims=" %%P in ('%PY% -c "import sys;print(sys.executable)"') do set "PYW=%%P"
powershell -NoProfile -ExecutionPolicy Bypass -File "%API_HOME%tools\make_shortcuts.ps1" -Pyw "%PYW%" -AppHome "%API_HOME:~0,-1%"
echo.
echo To pin it: press the Windows key, type ONE_MENU, right-click it, "Pin to taskbar".
echo Opening ONE_MENU now...
start "" "%PYW%" "%API_HOME%engine\web.py"

echo ==================================================
echo   Done. ONE_MENU is in your Start Menu and on your Desktop.
echo ==================================================
pause
