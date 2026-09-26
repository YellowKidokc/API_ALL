@echo off
rem Three Dials: understanding ON TOP, original article untouched below.
rem Drag an article onto this file, or run: 8_THREE_DIALS_ANNOTATE.bat "path\to\article.md"
pushd "%~dp0"
if "%~1"=="" (
  echo Drag an article onto this .bat
  pause
  exit /b 1
)
python -u "%~dp0SCRIPTS\three_dials_annotate.py" %*
echo.
echo Output: %~dp0OUTBOX\ANNOTATED_THREE_DIALS\
popd
pause
