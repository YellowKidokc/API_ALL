@echo off
setlocal
pushd "%~dp0" || exit /b 1
for %%D in (INBOX OUTBOX PROCESSED_ORIGINALS FAILED) do if not exist "%%D" mkdir "%%D"
if not exist "SCRIPTS\LOGS" mkdir "SCRIPTS\LOGS"
popd
exit /b 0
