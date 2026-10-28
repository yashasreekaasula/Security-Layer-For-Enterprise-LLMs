$ErrorActionPreference='Stop'; Set-Location (Split-Path -Parent $PSScriptRoot)
$env:PYTHONPATH="$PWD\backend"
& .\.venv\Scripts\python.exe -m pytest .\backend\tests -q
if ($LASTEXITCODE -ne 0) { throw 'Backend tests failed.' }
Push-Location .\frontend
npm test
if ($LASTEXITCODE -ne 0) { throw 'Frontend smoke tests failed.' }
npm run build
if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
Pop-Location
