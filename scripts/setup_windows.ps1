$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { throw 'Python was not found. Install Python 3.12 and reopen PowerShell.' }
if (-not (Test-Path '.venv')) { python -m venv .venv }
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r .\backend\requirements.txt
$env:PYTHONPATH="$PWD\backend"
& .\.venv\Scripts\python.exe -m alembic upgrade head
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { throw 'npm was not found. Install Node.js 20+ and reopen PowerShell.' }
Push-Location .\frontend
npm install
Pop-Location
Write-Host 'Setup complete. Next: .\.venv\Scripts\Activate.ps1'
