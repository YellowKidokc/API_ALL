@echo off
setlocal EnableDelayedExpansion
pushd "%~dp0" || (
  echo ERROR: Could not open EVIDENCE folder.
  pause
  exit /b 1
)

echo =========================================================================
echo  THEOPHYSICS AXIOM ONE-PAGE COMPILER & LEDGER EXTRACTOR (191 NODES)
echo =========================================================================
echo.
echo Compiles 191 Axiom nodes into ~55-70 line One-Page Axioms.
echo.

python -u "%~dp0SCRIPTS\axiom_one_page_transform.py" %*
set "EXIT_CODE=%ERRORLEVEL%"

echo.
echo Axiom compiler complete with status code: %EXIT_CODE%
echo.

popd
pause
exit /b %EXIT_CODE%
