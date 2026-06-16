from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path

import psycopg2


DB_CONFIG = {
    "dbname": os.getenv("PGDATABASE", "camera_ai"),
    "user": os.getenv("PGUSER", "postgres"),
    "password": os.getenv("PGPASSWORD", ""),
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", "5432")),
}

DETECTIONS_RETENTION_DAYS = int(os.getenv("DETECTIONS_RETENTION_DAYS", "7"))
EVENTS_RETENTION_DAYS = int(os.getenv("EVENTS_RETENTION_DAYS", "30"))
ALERTS_RETENTION_DAYS = int(os.getenv("ALERTS_RETENTION_DAYS", "30"))
SNAPSHOTS_RETENTION_DAYS = int(os.getenv("SNAPSHOTS_RETENTION_DAYS", "30"))
SNAPSHOT_DIR = Path(os.getenv("YOLO_POSTGRES_SNAPSHOT_DIR", "runs/postgres_snapshots"))


def cleanup_database() -> None:
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM detections WHERE created_at < NOW() - (%s * INTERVAL '1 day')",
                (DETECTIONS_RETENTION_DAYS,),
            )
            detections_deleted = cur.rowcount

            cur.execute(
                "DELETE FROM alerts WHERE created_at < NOW() - (%s * INTERVAL '1 day')",
                (ALERTS_RETENTION_DAYS,),
            )
            alerts_deleted = cur.rowcount

            cur.execute(
                "DELETE FROM detection_events WHERE end_time < NOW() - (%s * INTERVAL '1 day')",
                (EVENTS_RETENTION_DAYS,),
            )
            events_deleted = cur.rowcount

    print(f"Deleted detections: {detections_deleted}")
    print(f"Deleted alerts: {alerts_deleted}")
    print(f"Deleted events: {events_deleted}")


def cleanup_snapshots() -> None:
    if not SNAPSHOT_DIR.exists():
        print(f"Snapshot directory not found: {SNAPSHOT_DIR}")
        return

    cutoff = datetime.now() - timedelta(days=SNAPSHOTS_RETENTION_DAYS)
    deleted = 0

    for path in SNAPSHOT_DIR.glob("*.jpg"):
        if datetime.fromtimestamp(path.stat().st_mtime) < cutoff:
            path.unlink()
            deleted += 1

    print(f"Deleted snapshots: {deleted}")


def main() -> None:
    cleanup_database()
    cleanup_snapshots()


if __name__ == "__main__":
    main()
