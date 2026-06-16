Set-Location $PSScriptRoot

$env:PGDATABASE = "camera_ai"
$env:PGUSER = "postgres"
Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue

$env:DETECTIONS_RETENTION_DAYS = "7"
$env:EVENTS_RETENTION_DAYS = "30"
$env:ALERTS_RETENTION_DAYS = "30"
$env:SNAPSHOTS_RETENTION_DAYS = "30"

python .\cleanup_camera_data.py
