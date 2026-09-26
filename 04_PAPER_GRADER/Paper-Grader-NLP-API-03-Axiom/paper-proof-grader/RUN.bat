@echo off
setlocal
echo ============================================
echo  WORKFLOW: Paper Proof Grader
echo  Drop a paper into DROP_PAPERS_HERE, then run this.
echo ============================================

set PYTHON_EXE=C:\Users\lowes\AppData\Local\Programs\Python\Python313\python.exe
if not exist "%PYTHON_EXE%" set PYTHON_EXE=C:\Users\lowes\AppData\Local\Programs\Python\Python312\python.exe

if not exist "%~dp0pipeline.py" (
  echo Pipeline scaffold exists, but pipeline.py has not been built yet.
  echo See MASTER_VARIABLE_SCHEMA.md and README.md.
  pause
  exit /b 0
)

if exist "%PYTHON_EXE%" (
  "%PYTHON_EXE%" "%~dp0pipeline.py"
) else (
  py -3.13 "%~dp0pipeline.py"
)
set RC=%ERRORLEVEL%

echo ============================================
echo  Done (rc=%RC%). See X:\brain\_LOGS\workflow_paper-proof-grader_*.log
echo ============================================
pause
exit /b %RC%
