@echo off
setlocal EnableDelayedExpansion
pushd "%~dp0" || (
  echo ERROR: Could not open EVIDENCE folder.
  pause
  exit /b 1
)

echo =========================================================================
echo  FAITH THROUGH PHYSICS - SERIES GRAND SYNTHESIZER
echo =========================================================================
echo.

set /p SERIES_NAME="Enter Series Name (default: 01_THE_STORY): "
if "%SERIES_NAME%"=="" set "SERIES_NAME=01_THE_STORY"

echo.
echo Synthesizing series: %SERIES_NAME% ...
echo.

python -u "%~dp0SCRIPTS\series_grand_synthesizer.py" --series "%SERIES_NAME%" --provider openrouter %*
set "EXIT_CODE=%ERRORLEVEL%"

echo.
echo Synthesis completed with status code: %EXIT_CODE%
echo Check OUTBOX\FOR_SUBSTACK\ for the complete series overview.
echo Check OUTBOX\BY_SERIES\%SERIES_NAME%\ for the master synthesis paper.
echo.

popd
pause
exit /b %EXIT_CODE%
