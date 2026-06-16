# Real-Time Camera AI

This project extends Ultralytics YOLO with a local camera AI pipeline:

- Webcam object detection and tracking
- PostgreSQL storage for detections, events, and alerts
- Event snapshots
- FastAPI JSON endpoints
- Browser dashboard
- PowerShell run scripts for Windows

## Requirements

- Python 3.11+ or 3.13
- PostgreSQL
- Webcam
- Python packages:

```powershell
python -m pip install -e .
python -m pip install fastapi uvicorn psycopg2-binary opencv-python lap
```

## Database

Create the database and load the schema:

```powershell
createdb -U postgres camera_ai
psql -U postgres -d camera_ai -f sql/schema.sql
```

## Run

Start the API:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\run_api.ps1
```

Start YOLO tracking in another PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\run_yolo.ps1
```

Open:

```text
http://127.0.0.1:8000/dashboard
http://127.0.0.1:8000/health
```

## Endpoints

```text
GET  /
GET  /dashboard
GET  /health
GET  /active-events
GET  /webcam-summary
GET  /latest-detections
GET  /events
GET  /alerts
GET  /alerts/new
POST /alerts/{alert_id}/ack
GET  /snapshots/{filename}
```

## Runtime Scripts

```text
run_api.ps1      Start FastAPI dashboard
run_yolo.ps1     Start YOLO tracking with PostgreSQL logging
run_cleanup.ps1  Delete old detections/events/alerts/snapshots
```

## Notes

- `run_yolo.ps1` uses `yolo track`, not `yolo predict`, so `track_id` is stored when available.
- Default classes are `0,56,63`: person, chair, laptop.
- Default confidence is `0.5`.
- Snapshots are stored under `runs/postgres_snapshots`.
- Runtime outputs, snapshots, images, videos, and model weights are ignored by `.gitignore`.
