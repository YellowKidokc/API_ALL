@echo off
REM ==================================================================
REM  LEAN4 station - Axiom registry
REM  Order is fixed (each step uses the one before it):
REM    1 harvest   gather every distinct .lean file into H:\Desktop\ALL_LEAN4   (optional, slow)
REM    2 select    files that declare axioms; find their Lake project; set aside Mathlib tests
REM    3 compile   build each file in its own project + #print axioms for every theorem
REM    4 registry  dedupe, fact statuses, DeepSeek classification, one story
REM  Output: AXIOMS\  (pills by lane, registry csv/json, by-status/lane/spine, story)
REM ==================================================================
setlocal
pushd "%~dp0"
chcp 65001 >nul
set "PYTHONUTF8=1"
title LEAN4 - Axiom registry

set "ENGINE=%~dp0..\LEAN_ATOM_EXTRACTOR"
set "HARVEST=\\192.168.2.50\h_hp\Desktop\ALL_LEAN4"
set "OUT=%~dp0AXIOMS"

echo.
set "DOH="
set /p "DOH=1/4  Re-harvest all drives first? Takes 30+ minutes. (y/N) "
if /i "%DOH%"=="y" (
    python "%ENGINE%\harvest_lean.py" --dest "%HARVEST%" "D:\GitHub" "D:\TEMP_LEAN_ZIP" "D:\CHI PARTS" "D:\_AXIOM_WORK" "D:\DONT TOUCH HTML" "C:\Users\David\Documents" "C:\Users\David\SynologyDrive" "C:\theophysics" "C:\tpverify" "C:\Theophysics-Validation" "C:\Users\David\CrossDevice" "C:\Users\David\theophysics-read" "C:\Users\David\Desktop" "S:\" "\\192.168.2.50\h_hp\Desktop 2\LEAN 4" || goto :failed
)

echo.
echo 2/4  Selecting axiom files ...
python "%ENGINE%\axiom_select.py" "%HARVEST%" || goto :failed

echo.
echo 3/4  Compiling with Lean (#print axioms per theorem) - about an hour ...
python "%ENGINE%\axiom_compile.py" "%OUT%" 3 || goto :failed

echo.
echo 4/4  Building the registry (facts, then DeepSeek classification, then the story) ...
if defined DEEPSEEK_API_KEY (
    python "%ENGINE%\axiom_registry.py" "%OUT%" || goto :failed
) else (
    echo    DEEPSEEK_API_KEY not set - facts only
    python "%ENGINE%\axiom_registry.py" "%OUT%" --facts || goto :failed
)

echo.
echo Done. Opening %OUT%
start "" "%OUT%"
start "" "%OUT%\00_AXIOM_STORY.md"
pause
exit /b 0

:failed
echo.
echo Something failed - see the messages above.
pause
exit /b 1
