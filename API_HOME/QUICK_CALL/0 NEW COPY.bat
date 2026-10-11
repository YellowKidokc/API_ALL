@echo off
setlocal
rem Makes a fresh copy of this folder next to it: prompt and settings come along, input\ and output\ start empty.
set "NAME="
set /p "NAME=Name for the new copy: "
if not defined NAME exit /b 1
set "DEST=%~dp0..\%NAME%"
if exist "%DEST%" (echo "%DEST%" already exists. & pause & exit /b 1)
mkdir "%DEST%\input" "%DEST%\output"
for %%F in (call.py prompt.txt settings.txt README.txt RUN.bat DRY_RUN.bat "0 NEW COPY.bat") do copy /y "%~dp0%%~F" "%DEST%\" >nul
echo Made "%DEST%". Edit its prompt.txt, drop files in its input\, run its RUN.bat.
start "" "%DEST%"
