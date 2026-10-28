$ErrorActionPreference='Stop'; Set-Location (Split-Path -Parent $PSScriptRoot)
$env:PYTHONPATH="$PWD\backend"
& .\.venv\Scripts\python.exe -m app.train
if ($LASTEXITCODE -ne 0) { throw 'PPO training/evaluation failed.' }
Write-Host 'Checkpoint: models\privacy_ppo.pt'; Write-Host 'Reports: reports\evaluation_validation.json and reports\evaluation_test.json'
