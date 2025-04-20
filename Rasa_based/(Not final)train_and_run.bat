@echo off
echo Checking if retraining is necessary...
rasa train --dry-run > dry_run_output.txt
findstr /C:"No training required." dry_run_output.txt >nul
if %errorlevel%==0 (
    echo No changes detected. Skipping training.
) else (
    echo Changes detected. Training model...
    rasa train
)
echo Starting action server...
start rasa run actions
echo Starting Rasa server...
rasa run