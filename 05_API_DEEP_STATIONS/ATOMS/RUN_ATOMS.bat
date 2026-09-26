@echo off
setlocal enabledelayedexpansion

REM ATOMS station launcher — classify inbox sources into claim atoms.
REM Outputs Markdown companions to OUTBOX/01_ALL_PAPERS and JSON records to OUTBOX/06_JSON_RECORDS.

cd /d "%~dp0"
python "SCRIPTS\run_atoms.py" %*

pause
