$ErrorActionPreference='Stop'; Set-Location (Split-Path -Parent $PSScriptRoot)
$env:PYTHONPATH="$PWD\backend"
& .\.venv\Scripts\python.exe -m app.seed 3000 50000
if ($LASTEXITCODE -ne 0) { throw 'Synthetic data generation failed.' }
Write-Host 'Generated 3,000 employees and 50,000 knowledge documents.'
