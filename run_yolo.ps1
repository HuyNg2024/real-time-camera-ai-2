Set-Location $PSScriptRoot

if (-not $env:YOLO_POSTGRES) { $env:YOLO_POSTGRES = "1" }
if (-not $env:YOLO_POSTGRES_EVERY_N_FRAMES) { $env:YOLO_POSTGRES_EVERY_N_FRAMES = "30" }
if (-not $env:YOLO_POSTGRES_EVENT_GAP_SECONDS) { $env:YOLO_POSTGRES_EVENT_GAP_SECONDS = "10" }
if (-not $env:YOLO_POSTGRES_SAVE_SNAPSHOTS) { $env:YOLO_POSTGRES_SAVE_SNAPSHOTS = "1" }
if (-not $env:YOLO_CAMERA_ID) { $env:YOLO_CAMERA_ID = "webcam_01" }
if (-not $env:PGDATABASE) { $env:PGDATABASE = "camera_ai" }
if (-not $env:PGUSER) { $env:PGUSER = "postgres" }
if (-not $env:PGHOST) { $env:PGHOST = "localhost" }
if (-not $env:PGPORT) { $env:PGPORT = "5432" }

yolo track model=yolo11n.pt source=0 show=True conf=0.5 classes=0,56,63
