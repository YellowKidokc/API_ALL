@echo off
setlocal
pushd "%~dp0"
chcp 65001 >nul
set "PYTHONUTF8=1"
title Lean Atom Extractor

REM ------------------------------------------------------------------
REM  Which Lean project to scan. Point it at the folder that holds
REM  lakefile.lean + lean-toolchain (the project root), not a subfolder
REM  of notes. Drag a folder onto this .bat, or type/paste one below.
REM ------------------------------------------------------------------
set "DEFAULT_ROOT=D:\GitHub\Faith-Thru-Physics-Lean-4-"
set "PILLS=\\192.168.2.50\h_hp\Desktop\APIs\APIs\CLAIMS_PROOFS_EVIDENCE\PROOF"
set "ROOT=%~1"
if "%ROOT%"=="" (
    echo Lean project folder [Enter = %DEFAULT_ROOT%]
    set /p "ROOT=> "
)
if "%ROOT%"=="" set "ROOT=%DEFAULT_ROOT%"
set "ROOT=%ROOT:"=%"
if not exist "%ROOT%\" (
    echo.
    echo Folder not found: %ROOT%
    pause
    exit /b 1
)
if not exist "%ROOT%\lakefile.lean" if not exist "%ROOT%\lakefile.toml" (
    echo.
    echo NOTE: no lakefile in %ROOT%
    echo       Scanning still works, but "verify" needs a Lake project root.
)

set "LA=python -m lean_atom.cli --root "%ROOT%""

echo.
echo ==================================================================
echo  1/3  Scan .lean files (unchanged files are skipped)
echo ==================================================================
%LA% scan || goto :failed

echo.
echo ==================================================================
echo  2/3  Classify + trust audit (sorry / admit / axiom / unsafe)
echo ==================================================================
%LA% classify || goto :failed
%LA% audit || goto :failed

echo.
set "DOVERIFY="
set /p "DOVERIFY=3/3  Compile every file with Lean now? Slow the first time. (y/N) "
if /i "%DOVERIFY%"=="y" (
    pushd "%ROOT%"
    lake build
    popd
    %LA% verify
)

echo.
echo  Proof briefs (plain-language write-ups, DeepSeek; unchanged files are skipped)
if defined DEEPSEEK_API_KEY (
    %LA% briefs --out "%PILLS%"
) else (
    echo    DEEPSEEK_API_KEY not set - skipping briefs
)

echo.
echo  Writing pills (theorems + definitions, linked; scans other nodes for mentions)
%LA% pills --out "%PILLS%"

echo.
echo ==================================================================
echo  Dashboard:  this PC      http://127.0.0.1:8989
echo              other PCs   http://%COMPUTERNAME%:8989  or  http://192.168.2.51:8989
echo  (close this window to stop the dashboard)
echo ==================================================================
netstat -ano | findstr ":8989 " | findstr LISTENING >nul && (
    echo  The background Lean registry is already running - it will show the new results
    echo  after a restart of SERVE_LEAN_ATOM.bat. Opening it now.
    start "" http://127.0.0.1:8989
    pause
    goto :eof
)
start "" http://127.0.0.1:8989
%LA% serve --port 8989 --pills "%PILLS%"
goto :eof

:failed
echo.
echo Something went wrong - run TROUBLESHOOT_LEAN_ATOM.bat
pause
exit /b 1
