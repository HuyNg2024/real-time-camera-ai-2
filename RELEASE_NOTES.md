# Release Notes

## Real-Time Camera AI v1.0.1

First stable demo release for the Real-Time Camera AI project.

### Features

- Real-time YOLO webcam object detection
- PostgreSQL detection logging
- Object event grouping
- Snapshot capture for detected events
- Configurable alert rules
- Alert acknowledgement API
- FastAPI dashboard
- CSV export endpoints
- Docker Compose demo setup
- Demo seed data
- GitHub Actions CI

### Quick Start

Start Docker Desktop, then run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\reset_docker_demo.ps1
```

Open the dashboard:

```text
http://127.0.0.1:8000/dashboard
```

To connect a real webcam YOLO run to the Docker database:

```powershell
.\run_yolo_docker_db.ps1
```

### Notes

This project is based on the Ultralytics YOLO codebase and adds a camera AI pipeline with PostgreSQL, event tracking, alerts, snapshots, API endpoints, dashboard, Docker demo scripts, and CI.
