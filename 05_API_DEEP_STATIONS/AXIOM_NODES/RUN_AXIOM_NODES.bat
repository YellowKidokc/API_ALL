@echo off
setlocal enabledelayedexpansion

REM AXIOM_NODES station launcher — map papers to canonical axiom nodes.
REM Outputs enriched papers (axiom mapping appended) and JSON records to OUTBOX/06_JSON_RECORDS.

cd /d "%~dp0"
python "SCRIPTS\run_axiom_nodes.py" %*

pause
