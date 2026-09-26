@echo off
setlocal
pushd "%~dp0"
chcp 65001 >nul
set "PYTHONUTF8=1"
title Lean Atom Extractor - Troubleshoot

set "ROOT=%~1"
if "%ROOT%"=="" set "ROOT=D:\GitHub\Faith-Thru-Physics-Lean-4-"
set "ROOT=%ROOT:"=%"

echo ==================================================================
echo  Lean Atom Extractor - health check
echo  Project folder: %ROOT%
echo ==================================================================

echo.
echo [1] Python
python --version || echo    FIX: install Python 3.10+ and tick "Add to PATH"

echo.
echo [2] Python packages (pydantic, click, jinja2)
python -c "import pydantic, click, jinja2; print('   OK')" 2>nul || (
    echo    Missing - installing from requirements.txt ...
    python -m pip install -r requirements.txt
)

echo.
echo [3] lean_atom package loads
python -c "import lean_atom.cli; print('   OK')" || echo    FIX: run this .bat from the lean-atom-extractor folder

echo.
echo [4] Lean toolchain (elan / lean / lake)
where elan >nul 2>&1 && (elan --version) || echo    FIX: install elan from https://github.com/leanprover/elan
lean --version 2>nul || echo    lean not on PATH
lake --version 2>nul || echo    lake not on PATH

echo.
echo [5] Project folder
if exist "%ROOT%\" (echo    exists) else (echo    NOT FOUND - point the launcher at your Lean project root)
if exist "%ROOT%\lakefile.lean" echo    lakefile.lean found
if exist "%ROOT%\lakefile.toml" echo    lakefile.toml found
if not exist "%ROOT%\lakefile.lean" if not exist "%ROOT%\lakefile.toml" echo    no lakefile - verify will not work here (scan still does)
if exist "%ROOT%\lean-toolchain" (
    <nul set /p "=   project wants: "
    type "%ROOT%\lean-toolchain"
    echo.
    pushd "%ROOT%"
    <nul set /p "=   inside project, lean is: "
    lean --version 2>nul || echo (elan will download the toolchain on first lake build)
    popd
)

echo.
echo [6] Database
python -c "import sqlite3; c=sqlite3.connect('lean_atoms.db'); print('   declarations:', c.execute('select count(*) from declarations').fetchone()[0], '| builds recorded:', c.execute('select count(*) from builds').fetchone()[0])" 2>nul || echo    no database yet - run LAUNCH_LEAN_ATOM.bat

echo.
echo [7] Dashboard port 8989
netstat -ano | findstr ":8989 " | findstr LISTENING >nul && (echo    IN USE - a dashboard is already running, or close the program using it) || echo    free

echo.
echo [8] Tests
python -m pytest -q 2>nul | findstr /r "passed failed error" || echo    pytest not installed (optional: pip install pytest)

echo.
echo Done. Copy this window's text if you need help with a failure.
pause
