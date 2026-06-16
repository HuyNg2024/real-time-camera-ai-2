Set-Location $PSScriptRoot

if (-not $env:PGDATABASE) { $env:PGDATABASE = "camera_ai" }
if (-not $env:PGUSER) { $env:PGUSER = "postgres" }
if (-not $env:PGHOST) { $env:PGHOST = "localhost" }
if (-not $env:PGPORT) { $env:PGPORT = "5432" }

python -m uvicorn camera_api:app --host 127.0.0.1 --port 8000 --reload
