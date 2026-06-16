# Real-Time Camera AI

This project extends Ultralytics YOLO with a local camera AI pipeline:

- Webcam object detection and tracking
- PostgreSQL storage for detections, events, alerts, and alert rules
- Event snapshots
- FastAPI JSON endpoints
- Browser dashboard
- Dashboard charts for live monitoring
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

## Docker

Docker Compose runs PostgreSQL and the FastAPI dashboard. Webcam YOLO tracking should still run on Windows with `run_yolo.ps1`.
Start Docker Desktop first, then run:

```powershell
docker compose up --build
```

Open:

```text
http://127.0.0.1:8000/dashboard
```

The PostgreSQL container uses host port `5433`. To make host YOLO write to the Docker database:

```powershell
$env:PGHOST = "127.0.0.1"
$env:PGPORT = "5433"
$env:PGDATABASE = "camera_ai"
$env:PGUSER = "postgres"
$env:PGPASSWORD = "postgres"
.\run_yolo.ps1
```

## Endpoints

```text
GET  /
GET  /dashboard
GET  /health
GET  /runtime-config
GET  /active-events
GET  /webcam-summary
GET  /latest-detections
GET  /events
GET  /export/detections.csv
GET  /export/events.csv
GET  /export/alerts.csv
GET  /alerts
GET  /alerts/new
POST /alerts/{alert_id}/ack
POST /alerts/ack-all
GET  /alert-rules
POST /alert-rules
PATCH /alert-rules/{rule_id}
DELETE /alert-rules/{rule_id}
GET  /snapshots/{filename}
```

## Alert Rules

Alert creation is controlled by the `alert_rules` table. A rule matches by camera, object name, confidence, duration, and enabled state.

Default rule:

```text
camera_id=* object_name=person alert_type=person_detected min_confidence=0.5 min_duration_seconds=0
```

Example: add a cell phone alert rule:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/alert-rules `
  -ContentType "application/json" `
  -Body '{"camera_id":"*","object_name":"cell phone","alert_type":"phone_detected","min_confidence":0.7,"min_duration_seconds":0,"enabled":true,"message_template":"{object_name} detected on {camera_id}"}'
```

Rules can also be created from the `Alert Rules` panel on `/dashboard`.

## CSV Export Filters

CSV endpoints support `limit`, `camera_id`, `object_name`, and `hours`. Event and alert exports also support `status`.

```text
/export/detections.csv?object_name=person&camera_id=webcam_01&hours=24&limit=1000
/export/events.csv?status=active&object_name=person&limit=1000
/export/alerts.csv?status=new&object_name=cell phone&hours=24&limit=1000
```

## Runtime Scripts

```text
run_api.ps1      Start FastAPI dashboard
run_yolo.ps1     Start YOLO tracking with PostgreSQL logging
run_docker.ps1   Start PostgreSQL and API dashboard with Docker Compose
run_cleanup.ps1  Delete old detections/events/alerts/snapshots
test_system.ps1  Check Python, PostgreSQL, API, dashboard, and endpoints
```

## Notes

- `run_yolo.ps1` uses `yolo track`, not `yolo predict`, so `track_id` is stored when available.
- Default classes are `0,56,63`: person, chair, laptop.
- Default confidence is `0.5`.
- Snapshots are stored under `runs/postgres_snapshots`.
- Runtime outputs, snapshots, images, videos, and model weights are ignored by `.gitignore`.
