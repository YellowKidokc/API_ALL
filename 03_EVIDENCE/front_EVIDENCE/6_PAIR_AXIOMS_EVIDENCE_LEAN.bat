@echo off
setlocal EnableDelayedExpansion
pushd "%~dp0" || (
  echo ERROR: Could not open EVIDENCE folder.
  pause
  exit /b 1
)

echo =========================================================================
echo  THEOPHYSICS TRI-PARTITE CONGRUENCE & GAP PAIRING ENGINE
echo =========================================================================
echo.
echo Pairs One Story Truth Predicates with Evidence Sheets & Lean 4 Proofs.
echo.
echo Evidence Outbox: %~dp0OUTBOX\
echo Master Index:    %~dp0OUTBOX\04_MASTER_INDEX.tsv
echo Lean Floor:      %~dp0..\LEAN4\
echo.

python -u "%~dp0SCRIPTS\theophysics_congruence_matrix.py" %*
set "EXIT_CODE=%ERRORLEVEL%"

echo.
echo Congruence pairing complete with status code: %EXIT_CODE%
echo Outputs generated in OUTBOX\THEOPHYSICS_CONGRUENCE_MATRIX.md and .tsv
echo.

popd
pause
exit /b %EXIT_CODE%
