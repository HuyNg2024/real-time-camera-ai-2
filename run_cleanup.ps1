Set-Location $PSScriptRoot

if (-not $env:PGDATABASE) { $env:PGDATABASE = "camera_ai" }
if (-not $env:PGUSER) { $env:PGUSER = "postgres" }
if (-not $env:PGHOST) { $env:PGHOST = "localhost" }
if (-not $env:PGPORT) { $env:PGPORT = "5432" }

if (-not $env:DETECTIONS_RETENTION_DAYS) { $env:DETECTIONS_RETENTION_DAYS = "7" }
if (-not $env:EVENTS_RETENTION_DAYS) { $env:EVENTS_RETENTION_DAYS = "30" }
if (-not $env:ALERTS_RETENTION_DAYS) { $env:ALERTS_RETENTION_DAYS = "30" }
if (-not $env:SNAPSHOTS_RETENTION_DAYS) { $env:SNAPSHOTS_RETENTION_DAYS = "30" }

python .\cleanup_camera_data.py
