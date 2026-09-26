@echo off
rem API + ORIGINAL DOCUMENT MERGE
rem Finds every API output in OUTBOX, finds the original article it came from (by SHA-256),
rem and writes one file: API material on top, original article unchanged below.
rem Nothing is overwritten or moved. Output: OUTBOX\MERGED_WITH_ORIGINAL\
pushd "%~dp0"
python -u "%~dp0SCRIPTS\api_original_merge.py" %*
popd
pause
