@echo off
setlocal

set "ROOT=%~dp0"
cd /d "%ROOT%"
set "WORK_DIR=%ROOT%"

if not exist "config.txt" (
  echo Copy config.example.txt to config.txt and add API keys.
  exit /b 1
)

python feature_extractor.py --source-dir "%WORK_DIR%\INBOX"
if errorlevel 1 exit /b 1

python run_review_models.py --packets "features\feature_packets.jsonl"
if errorlevel 1 exit /b 1

for /d %%R in (reviews\run_*) do set "LATEST=%%R"
if not defined LATEST (
  echo No review run folder found in reviews\
  exit /b 1
)

python compare_reviews.py --packets "features\feature_packets.jsonl" --reviews "%LATEST%\model_reviews.jsonl"
if errorlevel 1 exit /b 1

echo Done.
endlocal
