@echo off
rem BEST ARGUMENTS + SHARED WEAKNESSES (no API calls)
rem Pulls each paper's arguments, truth predicates and weak links from the companions,
rem groups the ones that say the same thing across papers, and ranks the shared weaknesses.
rem Output: OUTBOX\BEST_ARGUMENTS\<timestamp>\REPORT.md  (+ CSVs to sort in Excel)
pushd "%~dp0"
python -u "%~dp0SCRIPTS\best_arguments_and_weaknesses.py" %*
for /f "delims=" %%d in ('dir /b /ad /o-n "%~dp0OUTBOX\BEST_ARGUMENTS"') do (
  start "" "%~dp0OUTBOX\BEST_ARGUMENTS\%%d\REPORT.md"
  goto :done
)
:done
popd
pause
