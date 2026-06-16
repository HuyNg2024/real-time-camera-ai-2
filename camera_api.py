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
    :root {
      --bg: #101113;
      --panel: #181a1f;
      --panel-2: #20232a;
      --line: #2b3038;
      --text: #eef2f7;
      --muted: #949ca8;
      --teal: #2dd4bf;
      --amber: #fbbf24;
      --rose: #fb7185;
      --violet: #a78bfa;
      --blue: #60a5fa;
      --green: #34d399;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      font-family: Inter, Segoe UI, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
    }
    .shell { display: grid; grid-template-columns: 232px minmax(0, 1fr); min-height: 100vh; }
    aside {
      border-right: 1px solid var(--line);
      background: #15171b;
      padding: 22px 16px;
      display: flex;
      flex-direction: column;
      gap: 22px;
    }
    .brand { display: flex; align-items: center; gap: 10px; font-weight: 700; letter-spacing: .2px; }
    .mark {
      width: 34px;
      height: 34px;
      border-radius: 8px;
      display: grid;
      place-items: center;
      background: linear-gradient(135deg, var(--teal), var(--violet));
      color: #081014;
      font-weight: 800;
    }
    nav { display: grid; gap: 6px; }
    nav a {
      display: flex;
      align-items: center;
      gap: 10px;
      color: var(--muted);
      text-decoration: none;
      padding: 10px 12px;
      border-radius: 6px;
      font-size: 14px;
    }
    nav a.active, nav a:hover { background: var(--panel-2); color: var(--text); }
    .side-status {
      margin-top: auto;
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: 8px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
    }
    main { min-width: 0; padding: 22px; display: grid; gap: 18px; }
    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 18px;
    }
    h1 { margin: 0; font-size: 22px; line-height: 1.2; }
    .toolbar { display: flex; align-items: center; gap: 12px; color: var(--muted); font-size: 13px; }
    .search {
      width: min(360px, 34vw);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px 12px;
      color: var(--text);
      background: var(--panel);
      outline: none;
    }
    .cards { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; }
    .card, section {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: 0 18px 36px rgba(0, 0, 0, .22);
    }
    .card { padding: 16px; min-height: 104px; display: grid; gap: 10px; }
    .card-label { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .08em; }
    .card-value { font-size: 26px; font-weight: 800; line-height: 1; }
    .card-detail { color: var(--muted); font-size: 13px; overflow-wrap: anywhere; }
    .accent-teal { border-top: 3px solid var(--teal); }
    .accent-amber { border-top: 3px solid var(--amber); }
    .accent-rose { border-top: 3px solid var(--rose); }
    .accent-violet { border-top: 3px solid var(--violet); }
    .grid { display: grid; grid-template-columns: minmax(0, 1.05fr) minmax(360px, .95fr); gap: 18px; align-items: start; }
    .stack { display: grid; gap: 18px; }
    section { overflow: hidden; }
    .section-head {
      min-height: 52px;
      padding: 14px 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid var(--line);
    }
    h2 { margin: 0; font-size: 15px; }
    .hint { color: var(--muted); font-size: 12px; }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th, td { padding: 11px 13px; border-bottom: 1px solid var(--line); text-align: left; white-space: nowrap; }
    th { color: var(--muted); background: #1b1e24; font-weight: 650; font-size: 12px; text-transform: uppercase; letter-spacing: .05em; }
    td { color: #dde3ec; }
    tr:last-child td { border-bottom: 0; }
    .table-wrap { max-width: 100%; overflow-x: auto; }
    .muted { color: var(--muted); }
    .pill {
      display: inline-flex;
      align-items: center;
      min-height: 22px;
      padding: 3px 8px;
      border-radius: 999px;
      background: rgba(96, 165, 250, .12);
      color: var(--blue);
      font-size: 12px;
      font-weight: 650;
    }
    .pill.new { background: rgba(251, 191, 36, .14); color: var(--amber); }
    .pill.closed { background: rgba(148, 156, 168, .14); color: #c1c7d0; }
    .pill.acknowledged { background: rgba(52, 211, 153, .12); color: var(--green); }
    button {
      border: 1px solid rgba(45, 212, 191, .45);
      background: rgba(45, 212, 191, .12);
      color: var(--teal);
      border-radius: 6px;
      padding: 6px 10px;
      cursor: pointer;
      font-weight: 650;
    }
    button:hover { background: rgba(45, 212, 191, .2); }
    a { color: var(--teal); text-decoration: none; }
    a:hover { text-decoration: underline; }
    .snapshot {
      min-height: 276px;
      display: grid;
      place-items: center;
      background: #0d0f12;
    }
    .snapshot img { width: 100%; height: 276px; object-fit: contain; display: block; }
    .snapshot-empty { color: var(--muted); padding: 24px; text-align: center; }
    @media (max-width: 1100px) {
      .shell { grid-template-columns: 1fr; }
      aside { display: none; }
      .cards { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .grid { grid-template-columns: 1fr; }
      .search { width: 42vw; }
    }
    @media (max-width: 640px) {
      main { padding: 14px; }
      header { align-items: flex-start; flex-direction: column; }
      .toolbar { width: 100%; justify-content: space-between; }
      .search { width: 100%; }
      .cards { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <aside>
      <div class="brand"><div class="mark">AI</div><span>Camera AI</span></div>
      <nav>
        <a class="active" href="/dashboard">Dashboard</a>
        <a href="/active-events">Active Events</a>
        <a href="/alerts">Alerts API</a>
        <a href="/latest-detections">Detections API</a>
      </nav>
      <div class="side-status">
        <div>Database: <span id="db-status">checking</span></div>
        <div>Refresh: 5 seconds</div>
        <div>Camera: webcam_01</div>
      </div>
    </aside>
    <main>
      <header>
        <div>
          <h1>Real-Time Camera AI Dashboard</h1>
          <div class="hint">YOLO detections, object events, snapshots and alerts</div>
        </div>
        <div class="toolbar">
          <input class="search" id="filter" type="search" placeholder="Filter object name">
          <span id="updated">Loading...</span>
        </div>
      </header>

      <div class="cards">
        <div class="card accent-amber">
          <div class="card-label">New Alerts</div>
          <div class="card-value" id="kpi-alerts">0</div>
          <div class="card-detail" id="kpi-alerts-detail">No pending alert</div>
        </div>
        <div class="card accent-teal">
          <div class="card-label">Active Tracks</div>
          <div class="card-value" id="kpi-active">0</div>
          <div class="card-detail" id="kpi-active-detail">No active object</div>
        </div>
        <div class="card accent-violet">
          <div class="card-label">Detections Last Hour</div>
          <div class="card-value" id="kpi-detections">0</div>
          <div class="card-detail" id="kpi-top-object">Top object: -</div>
        </div>
        <div class="card accent-rose">
          <div class="card-label">Latest Detection</div>
          <div class="card-value" id="kpi-latest">-</div>
          <div class="card-detail" id="kpi-latest-detail">Waiting for data</div>
        </div>
      </div>

      <div class="grid">
        <div class="stack">
          <section>
            <div class="section-head"><h2>Alerts</h2><span class="hint">Acknowledge from here</span></div>
            <div class="table-wrap"><table id="alerts"></table></div>
          </section>
          <section>
            <div class="section-head"><h2>Active Events</h2><span class="hint">Currently visible objects</span></div>
            <div class="table-wrap"><table id="active"></table></div>
          </section>
          <section>
            <div class="section-head"><h2>Latest Detections</h2><span class="hint">Raw YOLO rows</span></div>
            <div class="table-wrap"><table id="detections"></table></div>
          </section>
        </div>
        <div class="stack">
          <section>
            <div class="section-head"><h2>Latest Snapshot</h2><span class="hint" id="snapshot-title">No snapshot selected</span></div>
            <div class="snapshot" id="snapshot-preview"><div class="snapshot-empty">Snapshot appears here when an event has an image.</div></div>
          </section>
          <section>
            <div class="section-head"><h2>Webcam Summary - Last Hour</h2><span class="hint">Grouped by object</span></div>
            <div class="table-wrap"><table id="summary"></table></div>
          </section>
          <section>
            <div class="section-head"><h2>Recent Events</h2><span class="hint">Open and closed events</span></div>
            <div class="table-wrap"><table id="events"></table></div>
          </section>
        </div>
      </div>
    </main>
  </div>
  <script>
    function cell(value) {
      if (value === null || value === undefined || value === "") return '<span class="muted">-</span>';
      return String(value);
    }

    function fmt(value) {
      if (value === null || value === undefined || value === "") return "-";
      const num = Number(value);
      return Number.isFinite(num) ? num.toFixed(4) : String(value);
    }

    function time(value) {
      if (!value) return '<span class="muted">-</span>';
      const date = new Date(value);
      return Number.isNaN(date.getTime()) ? cell(value) : date.toLocaleString();
    }

    function snapshotUrl(path) {
      if (!path) return '<span class="muted">-</span>';
      const file = String(path).split(/[\\\\/]/).pop();
      return `/snapshots/${encodeURIComponent(file)}`;
    }

    function snapshotLink(path) {
      if (!path) return '<span class="muted">-</span>';
      return `<a href="${snapshotUrl(path)}" target="_blank">snapshot</a>`;
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

    function filtered(rows) {
      const q = document.getElementById('filter').value.trim().toLowerCase();
      if (!q) return rows;
      return rows.filter(row => String(row.object_name || '').toLowerCase().includes(q));
    }

    function updateKpis(health, alerts, active, summary, detections) {
      const newAlerts = alerts.filter(row => row.status === 'new');
      const totalDetections = summary.reduce((sum, row) => sum + Number(row.total_detections || 0), 0);
      const top = summary[0];
      const latest = detections[0];

      document.getElementById('kpi-alerts').textContent = newAlerts.length;
      document.getElementById('kpi-alerts-detail').textContent = newAlerts[0] ? `${newAlerts[0].object_name} on ${newAlerts[0].camera_id}` : 'No pending alert';
      document.getElementById('kpi-active').textContent = active.length;
      document.getElementById('kpi-active-detail').textContent = active.length ? active.map(row => row.object_name).join(', ') : 'No active object';
      document.getElementById('kpi-detections').textContent = totalDetections;
      document.getElementById('kpi-top-object').textContent = top ? `Top object: ${top.object_name} (${top.total_detections})` : 'Top object: -';
      document.getElementById('kpi-latest').textContent = latest ? latest.object_name : '-';
      document.getElementById('kpi-latest-detail').textContent = latest ? `conf ${fmt(latest.confidence)} at frame ${cell(latest.frame_id)}` : 'Waiting for data';
      document.getElementById('db-status').textContent = health.database || 'unknown';
    }

    function updateSnapshot(rows) {
      const row = rows.find(item => item.snapshot_path);
      const preview = document.getElementById('snapshot-preview');
      const title = document.getElementById('snapshot-title');
      if (!row) {
        preview.innerHTML = '<div class="snapshot-empty">Snapshot appears here when an event has an image.</div>';
        title.textContent = 'No snapshot selected';
        return;
      }
      title.textContent = `${row.object_name} / ${row.status || 'event'}`;
      preview.innerHTML = `<a href="${snapshotUrl(row.snapshot_path)}" target="_blank"><img src="${snapshotUrl(row.snapshot_path)}" alt="Detection snapshot"></a>`;
    }

    async function load() {
      const [health, alerts, active, summary, events, detections] = await Promise.all([
        fetch('/health').then(r => r.json()),
        fetch('/alerts').then(r => r.json()),
        fetch('/active-events').then(r => r.json()),
        fetch('/webcam-summary').then(r => r.json()),
        fetch('/events?limit=20').then(r => r.json()),
        fetch('/latest-detections?limit=20').then(r => r.json())
      ]);

      const viewAlerts = filtered(alerts);
      const viewActive = filtered(active);
      const viewSummary = filtered(summary);
      const viewEvents = filtered(events);
      const viewDetections = filtered(detections);

      updateKpis(health, alerts, active, summary, detections);
      updateSnapshot([...active, ...events]);

      renderTable('alerts', viewAlerts, [
        { key: 'type', label: 'Type', render: v => `<span class="pill new">${cell(v)}</span>` },
        { key: 'camera_id', label: 'Camera' },
        { key: 'object_name', label: 'Object' },
        { key: 'track_id', label: 'Track ID' },
        { key: 'confidence', label: 'Confidence', render: fmt },
        { key: 'status', label: 'Status', render: v => `<span class="pill ${cell(v)}">${cell(v)}</span>` },
        { key: 'created_at', label: 'Created', render: time },
        { key: 'message', label: 'Message' },
        { key: 'id', label: 'Action', render: (id, row) => row.status === 'new' ? `<button onclick="ackAlert(${id})">ACK</button>` : '-' }
      ]);

      renderTable('active', viewActive, [
        { key: 'object_name', label: 'Object' },
        { key: 'track_id', label: 'Track ID' },
        { key: 'detection_count', label: 'Count' },
        { key: 'max_confidence', label: 'Max Conf', render: fmt },
        { key: 'last_confidence', label: 'Last Conf', render: fmt },
        { key: 'duration_seconds', label: 'Duration (s)' },
        { key: 'snapshot_path', label: 'Snapshot', render: snapshotLink }
      ]);

      renderTable('summary', viewSummary, [
        { key: 'object_name', label: 'Object' },
        { key: 'total_detections', label: 'Detections' },
        { key: 'max_confidence', label: 'Max Conf', render: fmt },
        { key: 'last_seen', label: 'Last Seen', render: time }
      ]);

      renderTable('events', viewEvents, [
        { key: 'object_name', label: 'Object' },
        { key: 'track_id', label: 'Track ID' },
        { key: 'status', label: 'Status', render: v => `<span class="pill ${v === 'closed' ? 'closed' : ''}">${cell(v)}</span>` },
        { key: 'detection_count', label: 'Count' },
        { key: 'max_confidence', label: 'Max Conf', render: fmt },
        { key: 'snapshot_path', label: 'Snapshot', render: snapshotLink }
      ]);

      renderTable('detections', viewDetections, [
        { key: 'object_name', label: 'Object' },
        { key: 'track_id', label: 'Track ID' },
        { key: 'confidence', label: 'Conf', render: fmt },
        { key: 'frame_id', label: 'Frame' },
        { key: 'created_at', label: 'Created', render: time }
      ]);

      document.getElementById('updated').textContent = 'Updated ' + new Date().toLocaleTimeString();
    }

    document.getElementById('filter').addEventListener('input', load);
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
