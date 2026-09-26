@echo off
setlocal EnableDelayedExpansion
pushd "%~dp0" || (
  echo ERROR: Could not open EVIDENCE folder.
  pause
  exit /b 1
)

echo =========================================================================
echo  EVIDENCE ENGINE - 12X TURBO PARALLEL INTAKE (DEEPSEEK DIRECT)
echo =========================================================================
echo.
echo Target Inbox:  %~dp0INBOX\
echo Target Outbox: %~dp0OUTBOX\
echo Provider:      DeepSeek Direct API (deepseek-chat)
echo Workers:       12 Parallel Workers
echo.

python -u "%~dp0SCRIPTS\turbo_pipeline_runner.py" --workers 12 --provider deepseek %*
set "EXIT_CODE=%ERRORLEVEL%"

echo.
echo Process completed with status code: %EXIT_CODE%
echo Companions generated in OUTBOX\FOR_SUBSTACK\
echo.

popd
pause
exit /b %EXIT_CODE%
