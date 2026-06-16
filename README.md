# Real-Time Camera AI

Real-time webcam object detection and tracking built on Ultralytics YOLO, PostgreSQL, and FastAPI.

This repository turns a webcam feed into a small camera AI system:

- Detect and track objects with YOLO
- Store raw detections in PostgreSQL
- Group detections into events
- Save event snapshots
- Create configurable object alerts
- Acknowledge alerts from an API/dashboard
- View live status in a browser dashboard

## Features

- YOLO tracking with `track_id`
- PostgreSQL tables for `detections`, `detection_events`, `alerts`, and `alert_rules`
- Active event and hourly summary views
- Snapshot image storage for new events
- Database-driven alert rules with confidence and duration thresholds
- FastAPI endpoints and dashboard
- Dashboard charts for object counts, alert status, and confidence
- PowerShell scripts for Windows operation
- Cleanup script for old data and snapshots

## Quick Start

Install dependencies:

```powershell
python -m pip install -e .
python -m pip install fastapi uvicorn psycopg2-binary opencv-python lap
```

Create the PostgreSQL database and schema:

```powershell
createdb -U postgres camera_ai
psql -U postgres -d camera_ai -f sql/schema.sql
```

Start the API:

```powershell
cd real-time-camera-ai
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\run_api.ps1
```

Start YOLO tracking in another PowerShell:

```powershell
cd real-time-camera-ai
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\run_yolo.ps1
```

Open the dashboard:

```text
http://127.0.0.1:8000/dashboard
```

Health check:

```text
http://127.0.0.1:8000/health
```

## Documentation

See [CAMERA_AI_README.md](CAMERA_AI_README.md) for full setup instructions, including PostgreSQL schema, views, endpoints, and runtime notes.

## Main Scripts

```text
run_api.ps1      Start FastAPI dashboard
run_yolo.ps1     Start YOLO tracking with PostgreSQL logging
run_cleanup.ps1  Delete old detections/events/alerts/snapshots
```

## API Endpoints

```text
GET  /dashboard
GET  /health
GET  /active-events
GET  /webcam-summary
GET  /latest-detections
GET  /events
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

The default schema creates a person alert rule:

```text
camera_id=* object_name=person alert_type=person_detected min_confidence=0.5
```

Create or update a rule with:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/alert-rules `
  -ContentType "application/json" `
  -Body '{"camera_id":"*","object_name":"cell phone","alert_type":"phone_detected","min_confidence":0.7,"min_duration_seconds":0,"enabled":true,"message_template":"{object_name} detected on {camera_id}"}'
```

Rules can also be created from the `Alert Rules` panel on `/dashboard`.

## Notes

- This project is based on the Ultralytics YOLO codebase.
- Runtime outputs such as snapshots, `runs/`, images, videos, and model weights are ignored by `.gitignore`.
- Default tracked classes are `person`, `chair`, and `laptop`.
