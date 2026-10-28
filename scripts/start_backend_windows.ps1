$ErrorActionPreference='Stop'; Set-Location (Split-Path -Parent $PSScriptRoot)
$env:PYTHONPATH="$PWD\backend"
& .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
