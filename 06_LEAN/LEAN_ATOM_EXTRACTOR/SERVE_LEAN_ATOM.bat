@echo off
REM Start only the Lean dashboard + API (no scan). Nerve's tray item
REM "Lean 4 Registry (Port 8989)" opens it. Leave this window minimized.
setlocal
pushd "%~dp0"
chcp 65001 >nul
set "PYTHONUTF8=1"
title Lean Atom Registry - port 8989
set "PILLS=\\192.168.2.50\h_hp\Desktop\APIs\APIs\CLAIMS_PROOFS_EVIDENCE\PROOF"

netstat -ano | findstr ":8989 " | findstr LISTENING >nul && (
    echo Lean registry is already running on port 8989.
    timeout /t 3 >nul
    exit /b 0
)

echo Lean registry:  this PC http://127.0.0.1:8989   other PCs http://192.168.2.51:8989
python -m lean_atom.cli serve --port 8989 --pills "%PILLS%"
