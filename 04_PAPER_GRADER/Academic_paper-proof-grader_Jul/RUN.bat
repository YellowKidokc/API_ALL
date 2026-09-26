@echo off
setlocal

echo ============================================
echo  Paper Proof Grader
echo  Drop a paper into DROP_PAPERS_HERE, then run this.
echo ============================================

cd /d "%~dp0"
py -3 pipeline.py
if errorlevel 1 (
  python pipeline.py
)
set RC=%ERRORLEVEL%

echo ============================================
echo  Done (rc=%RC%). See LOGS for run logs.
echo ============================================
pause
exit /b %RC%
