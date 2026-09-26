@echo off
pushd "%~dp0"
echo =========================================================================
echo  EVIDENCE INTAKE PIPELINE HEALTHCHECK
echo =========================================================================
python "%~dp0SCRIPTS\healthcheck.py"
popd
pause
