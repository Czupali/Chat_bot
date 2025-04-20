# Beállítások
$watchFiles = @("data\nlu.yml", "domain.yml", "config.yml", "data\rules.yml", "data\stories.yml")
$modelDir = "models"
$latestModel = Get-ChildItem "$modelDir\*.tar.gz" | Sort-Object LastWriteTime -Descending | Select-Object -First 1

function NeedsRetraining {
    foreach ($file in $watchFiles) {
        if ((Test-Path $file) -and ($latestModel -eq $null -or (Get-Item $file).LastWriteTime -gt $latestModel.LastWriteTime)) {
            return $true
        }
    }
    return $false
}

Write-Host " Checking if model retraining is necessary..." -ForegroundColor Yellow

if (NeedsRetraining) {
    Write-Host "🚀 Training model..." -ForegroundColor Green
    rasa train
} else {
    Write-Host " Model is up-to-date. Skipping training." -ForegroundColor Cyan
}

Write-Host ""
Write-Host " Starting action server in new window..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "rasa run actions"

Start-Sleep -Seconds 3

Write-Host ""
Write-Host " Starting Rasa shell..." -ForegroundColor Green
rasa shell
