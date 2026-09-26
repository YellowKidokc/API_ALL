@echo off
rem BUILD ONE ARGUMENT UP (DeepSeek)
rem Makes OUTBOX\ARGUMENTS\<argument>\ , copies every paper that makes the argument into papers\,
rem judges originality, traces where it comes from, and gives labeled build steps, quotes and sources.
rem Run it again on the same argument for the next, deeper round.
pushd "%~dp0"
set /p ARG=Argument to build (e.g. Logic comes from God):
echo.
echo Matching argument groups:
python -u "%~dp0SCRIPTS\argument_builder.py" --find "%ARG%" --list
echo.
set /p RANKS=Extra group numbers from the report to include (blank for none):
python -u "%~dp0SCRIPTS\argument_builder.py" --find "%ARG%" --name "%ARG%" --ranks %RANKS%
for /f "delims=" %%d in ('dir /b /ad /o-d "%~dp0OUTBOX\ARGUMENTS"') do (
  start "" "%~dp0OUTBOX\ARGUMENTS\%%d\BUILD_LATEST.md"
  goto :done
)
:done
popd
pause
