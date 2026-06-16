Set-Location $PSScriptRoot

$env:YOLO_POSTGRES = "1"
$env:YOLO_POSTGRES_EVERY_N_FRAMES = "30"
$env:YOLO_POSTGRES_EVENT_GAP_SECONDS = "10"
$env:YOLO_POSTGRES_SAVE_SNAPSHOTS = "1"
$env:YOLO_CAMERA_ID = "webcam_01"
$env:PGDATABASE = "camera_ai"
$env:PGUSER = "postgres"
Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue

yolo track model=yolo11n.pt source=0 show=True conf=0.5 classes=0,56,63
