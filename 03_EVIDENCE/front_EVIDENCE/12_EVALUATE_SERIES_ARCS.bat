@echo off
REM ═══════════════════════════════════════════════════
REM  SERIES EVALUATOR — Grade each series as a SERIES
REM  Runs DeepSeek by default, 12 parallel
REM  Output: SERIES_SCORECARD.md, SERIES_ARC_REPORT.md
REM  in each BY_SERIES/<name>/ folder
REM ═══════════════════════════════════════════════════

cd /d "%~dp0"

echo.
echo  ╔═══════════════════════════════════════════╗
echo  ║   SERIES EVALUATOR ^& ARC GRADER v1.0     ║
echo  ║   DeepSeek default ^| 12 parallel          ║
echo  ╚═══════════════════════════════════════════╝
echo.

REM Run all series
python SCRIPTS\series_evaluator.py --all --provider deepseek --workers 12

echo.
echo  Done. Check BY_SERIES folders for:
echo    - SERIES_SCORECARD.md
echo    - SERIES_ARC_REPORT.md
echo    - SERIES_REORDER_RECOMMENDATION.md (if needed)
echo.
pause
