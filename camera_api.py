from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import psycopg2
import psycopg2.extras
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse


app = FastAPI(title="Camera AI API")

DB_CONFIG = {
    "dbname": os.getenv("PGDATABASE", "camera_ai"),
    "user": os.getenv("PGUSER", "postgres"),
    "password": os.getenv("PGPASSWORD", ""),
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", "5432")),
}

DASHBOARD_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Camera AI Dashboard</title>
  <style>
    body { margin: 0; font-family: Arial, sans-serif; background: #f6f7f9; color: #1f2937; }
    header { padding: 16px 24px; background: #111827; color: #fff; display: flex; justify-content: space-between; }
    main { padding: 20px 24px; display: grid; gap: 20px; }
    section { background: #fff; border: 1px solid #d8dde6; border-radius: 6px; overflow: hidden; }
    h2 { margin: 0; padding: 12px 14px; font-size: 16px; border-bottom: 1px solid #e5e7eb; }
    table { width: 100%; border-collapse: collapse; font-size: 14px; }
    th, td { padding: 10px 12px; border-bottom: 1px solid #edf0f4; text-align: left; white-space: nowrap; }
    th { background: #f9fafb; font-weight: 600; }
    tr:last-child td { border-bottom: 0; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
    .muted { color: #6b7280; }
    .pill { display: inline-block; padding: 2px 8px; border-radius: 999px; background: #e8f1ff; color: #1d4ed8; }
    .alert { background: #fff7ed; color: #9a3412; }
    .closed { background: #f3f4f6; color: #4b5563; }
    .table-wrap { overflow-x: auto; }
    button { border: 1px solid #cbd5e1; background: #fff; border-radius: 4px; padding: 5px 8px; cursor: pointer; }
    button:hover { background: #f8fafc; }
    a { color: #1d4ed8; text-decoration: none; }
    @media (max-width: 900px) { .grid { grid-template-columns: 1fr; } header { display: block; } }
  </style>
</head>
<body>
  <header>
    <div>Camera AI Dashboard</div>
    <div class="muted" id="updated">Loading...</div>
  </header>
  <main>
    <section>
      <h2>Alerts</h2>
      <div class="table-wrap"><table id="alerts"></table></div>
    </section>
    <section>
      <h2>Active Events</h2>
      <div class="table-wrap"><table id="active"></table></div>
    </section>
    <div class="grid">
      <section>
        <h2>Webcam Summary - Last Hour</h2>
        <div class="table-wrap"><table id="summary"></table></div>
      </section>
      <section>
        <h2>Recent Events</h2>
        <div class="table-wrap"><table id="events"></table></div>
      </section>
    </div>
    <section>
      <h2>Latest Detections</h2>
      <div class="table-wrap"><table id="detections"></table></div>
    </section>
  </main>
  <script>
    function cell(value) {
      if (value === null || value === undefined || value === "") return '<span class="muted">-</span>';
      return String(value);
    }

    function snapshotLink(path) {
      if (!path) return '<span class="muted">-</span>';
      const file = String(path).split(/[\\\\/]/).pop();
      return `<a href="/snapshots/${encodeURIComponent(file)}" target="_blank">snapshot</a>`;
    }

    function renderTable(id, rows, columns) {
      const table = document.getElementById(id);
      const head = '<tr>' + columns.map(c => `<th>${c.label}</th>`).join('') + '</tr>';
      const body = rows.length
        ? rows.map(row => '<tr>' + columns.map(c => `<td>${c.render ? c.render(row[c.key], row) : cell(row[c.key])}</td>`).join('') + '</tr>').join('')
        : `<tr><td colspan="${columns.length}" class="muted">No data</td></tr>`;
      table.innerHTML = head + body;
    }

    async function ackAlert(id) {
      await fetch(`/alerts/${id}/ack`, { method: 'POST' });
      await load();
    }

    async function load() {
      const [alerts, active, summary, events, detections] = await Promise.all([
        fetch('/alerts').then(r => r.json()),
        fetch('/active-events').then(r => r.json()),
        fetch('/webcam-summary').then(r => r.json()),
        fetch('/events?limit=20').then(r => r.json()),
        fetch('/latest-detections?limit=20').then(r => r.json())
      ]);

      renderTable('alerts', alerts, [
        { key: 'type', label: 'Type', render: v => `<span class="pill alert">${cell(v)}</span>` },
        { key: 'camera_id', label: 'Camera' },
        { key: 'object_name', label: 'Object' },
        { key: 'track_id', label: 'Track ID' },
        { key: 'confidence', label: 'Confidence' },
        { key: 'status', label: 'Status' },
        { key: 'created_at', label: 'Created' },
        { key: 'message', label: 'Message' },
        { key: 'id', label: 'Action', render: (id, row) => row.status === 'new' ? `<button onclick="ackAlert(${id})">ACK</button>` : '-' }
      ]);

      renderTable('active', active, [
        { key: 'object_name', label: 'Object' },
        { key: 'track_id', label: 'Track ID' },
        { key: 'detection_count', label: 'Count' },
        { key: 'max_confidence', label: 'Max Conf' },
        { key: 'last_confidence', label: 'Last Conf' },
        { key: 'duration_seconds', label: 'Duration (s)' },
        { key: 'snapshot_path', label: 'Snapshot', render: snapshotLink }
      ]);

      renderTable('summary', summary, [
        { key: 'object_name', label: 'Object' },
        { key: 'total_detections', label: 'Detections' },
        { key: 'max_confidence', label: 'Max Conf' },
        { key: 'last_seen', label: 'Last Seen' }
      ]);

      renderTable('events', events, [
        { key: 'object_name', label: 'Object' },
        { key: 'track_id', label: 'Track ID' },
        { key: 'status', label: 'Status', render: v => `<span class="pill ${v === 'closed' ? 'closed' : ''}">${cell(v)}</span>` },
        { key: 'detection_count', label: 'Count' },
        { key: 'max_confidence', label: 'Max Conf' },
        { key: 'snapshot_path', label: 'Snapshot', render: snapshotLink }
      ]);

      renderTable('detections', detections, [
        { key: 'object_name', label: 'Object' },
        { key: 'track_id', label: 'Track ID' },
        { key: 'confidence', label: 'Conf' },
        { key: 'frame_id', label: 'Frame' },
        { key: 'created_at', label: 'Created' }
      ]);

      document.getElementById('updated').textContent = 'Updated ' + new Date().toLocaleTimeString();
    }

    load();
    setInterval(load, 5000);
  </script>
</body>
</html>
"""


def query(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]


def execute(sql: str, params: tuple[Any, ...] = ()) -> int:
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.rowcount


@app.get("/", response_class=HTMLResponse)
def root() -> str:
    return DASHBOARD_HTML


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard() -> str:
    return DASHBOARD_HTML


@app.get("/health")
def health() -> dict[str, Any]:
    rows = query(
        """
        SELECT
            (SELECT COUNT(*) FROM new_alerts) AS new_alerts,
            (SELECT COUNT(*) FROM active_detection_events) AS active_events,
            (SELECT MAX(created_at) FROM detections) AS latest_detection_at
        """
    )
    row = rows[0]
    return {
        "api": "ok",
        "database": "ok",
        "new_alerts": row["new_alerts"],
        "active_events": row["active_events"],
        "latest_detection_at": row["latest_detection_at"],
    }


@app.get("/active-events")
def active_events() -> list[dict[str, Any]]:
    return query("SELECT * FROM active_detection_events")


@app.get("/alerts")
def alerts() -> list[dict[str, Any]]:
    return query(
        """
        SELECT id, camera_id, alert_type AS type, object_name, track_id, event_id, message,
               confidence, snapshot_path, status, created_at
        FROM alerts
        ORDER BY created_at DESC
        LIMIT 50
        """
    )


@app.get("/alerts/new")
def new_alerts() -> list[dict[str, Any]]:
    return query(
        """
        SELECT id, camera_id, alert_type AS type, object_name, track_id, event_id, message,
               confidence, snapshot_path, status, created_at
        FROM new_alerts
        """
    )


@app.post("/alerts/{alert_id}/ack")
def acknowledge_alert(alert_id: int) -> dict[str, Any]:
    rowcount = execute(
        """
        UPDATE alerts
        SET status = 'acknowledged'
        WHERE id = %s
        """,
        (alert_id,),
    )
    if rowcount == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"id": alert_id, "status": "acknowledged"}


@app.get("/webcam-summary")
def webcam_summary() -> list[dict[str, Any]]:
    return query("SELECT * FROM webcam_summary_last_hour")


@app.get("/latest-detections")
def latest_detections(limit: int = 50) -> list[dict[str, Any]]:
    limit = min(max(limit, 1), 500)
    return query(
        """
        SELECT id, camera_id, object_name, track_id, confidence, x1, y1, x2, y2, image_path, model_name, frame_id, created_at
        FROM detections
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (limit,),
    )


@app.get("/events")
def events(limit: int = 50) -> list[dict[str, Any]]:
    limit = min(max(limit, 1), 500)
    return query(
        """
        SELECT id, camera_id, object_name, track_id, status, detection_count, max_confidence, last_confidence,
               snapshot_path, start_time, end_time
        FROM detection_events
        ORDER BY end_time DESC
        LIMIT %s
        """,
        (limit,),
    )


@app.get("/snapshots/{path:path}")
def snapshot(path: str) -> FileResponse:
    snapshot_path = Path("runs/postgres_snapshots") / path
    resolved = snapshot_path.resolve()
    root = Path("runs/postgres_snapshots").resolve()

    if root not in resolved.parents and resolved != root:
        raise HTTPException(status_code=400, detail="Invalid snapshot path")
    if not resolved.is_file():
        raise HTTPException(status_code=404, detail="Snapshot not found")

    return FileResponse(resolved)
