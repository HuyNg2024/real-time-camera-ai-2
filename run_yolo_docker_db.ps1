Set-Location $PSScriptRoot

$env:PGHOST = "127.0.0.1"
$env:PGPORT = "15432"
$env:PGDATABASE = "camera_ai"
$env:PGUSER = "postgres"
$env:PGPASSWORD = "postgres"

.\run_yolo.ps1
