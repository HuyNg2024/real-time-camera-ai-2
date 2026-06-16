Set-Location $PSScriptRoot

$env:PGDATABASE = "camera_ai"
$env:PGUSER = "postgres"
Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue

python -m uvicorn camera_api:app --host 127.0.0.1 --port 8000 --reload
