# Ultralytics 🚀 AGPL-3.0 License - https://ultralytics.com/license

from __future__ import annotations

import os
from pathlib import Path

import cv2


_CONN = None
EVENT_GAP_SECONDS = int(os.getenv("YOLO_POSTGRES_EVENT_GAP_SECONDS", "10"))
SNAPSHOT_DIR = Path(os.getenv("YOLO_POSTGRES_SNAPSHOT_DIR", "runs/postgres_snapshots"))


def enabled() -> bool:
    """Return True when PostgreSQL detection logging is enabled."""
    return os.getenv("YOLO_POSTGRES", "0") == "1"


def _connect():
    """Create a lazy PostgreSQL connection only when detection logging is enabled."""
    global _CONN
    if _CONN is None:
        import psycopg2

        _CONN = psycopg2.connect(
            dbname=os.getenv("PGDATABASE", "camera_ai"),
            user=os.getenv("PGUSER", "postgres"),
            password=os.getenv("PGPASSWORD", ""),
            host=os.getenv("PGHOST", "localhost"),
            port=int(os.getenv("PGPORT", "5432")),
        )
    return _CONN


def _close_stale_events(cur) -> None:
    """Close active events that have not been seen recently."""
    cur.execute(
        """
        UPDATE detection_events
        SET status = 'closed'
        WHERE status = 'active'
          AND end_time < NOW() - (%s * INTERVAL '1 second')
        """,
        (EVENT_GAP_SECONDS,),
    )


def _save_snapshot(orig_img, camera_id: str, object_name: str, frame_id: int) -> str:
    """Save a snapshot image for a newly created event."""
    if orig_img is None or os.getenv("YOLO_POSTGRES_SAVE_SNAPSHOTS", "1") != "1":
        return ""

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    safe_object_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in object_name)
    path = SNAPSHOT_DIR / f"{camera_id}_{safe_object_name}_{frame_id}.jpg"
    cv2.imwrite(str(path), orig_img)
    return str(path)


def _insert_alert(
    cur,
    event_id: int,
    camera_id: str,
    object_name: str,
    confidence: float,
    snapshot_path: str,
    track_id: int | None,
) -> None:
    """Insert a single alert for a newly created event."""
    if object_name != "person":
        return

    alert_type = "person_detected"
    track_text = f" track {track_id}" if track_id is not None else ""
    cur.execute(
        """
        INSERT INTO alerts
        (camera_id, alert_type, object_name, event_id, message, confidence, snapshot_path, track_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (event_id, alert_type) WHERE event_id IS NOT NULL DO NOTHING
        """,
        (
            camera_id,
            alert_type,
            object_name,
            event_id,
            f"Person{track_text} detected on {camera_id}",
            confidence,
            snapshot_path,
            track_id,
        ),
    )


def _upsert_detection_event(cur, row: tuple, orig_img=None) -> None:
    """Create or update a detection event for one inserted detection row."""
    (
        camera_id,
        class_id,
        object_name,
        confidence,
        _x1,
        _y1,
        _x2,
        _y2,
        _image_path,
        model_name,
        frame_id,
        track_id,
    ) = row

    cur.execute(
        """
        WITH active_event AS (
            SELECT id
            FROM detection_events
            WHERE camera_id = %s
              AND class_id = %s
              AND object_name = %s
              AND model_name = %s
              AND track_id IS NOT DISTINCT FROM %s
              AND status = 'active'
              AND end_time >= NOW() - (%s * INTERVAL '1 second')
            ORDER BY end_time DESC
            LIMIT 1
        )
        UPDATE detection_events e
        SET end_time = NOW(),
            last_frame_id = %s,
            detection_count = detection_count + 1,
            max_confidence = GREATEST(max_confidence, %s),
            last_confidence = %s
        FROM active_event
        WHERE e.id = active_event.id
        RETURNING e.id
        """,
        (
            camera_id,
            class_id,
            object_name,
            model_name,
            track_id,
            EVENT_GAP_SECONDS,
            frame_id,
            confidence,
            confidence,
        ),
    )
    if cur.fetchone():
        return

    snapshot_path = _save_snapshot(orig_img, camera_id, object_name, frame_id)
    cur.execute(
        """
        INSERT INTO detection_events
        (
            camera_id, class_id, object_name, model_name, track_id, first_frame_id, last_frame_id,
            max_confidence, last_confidence, snapshot_path
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (
            camera_id,
            class_id,
            object_name,
            model_name,
            track_id,
            frame_id,
            frame_id,
            confidence,
            confidence,
            snapshot_path,
        ),
    )
    event_id = cur.fetchone()[0]
    _insert_alert(cur, event_id, camera_id, object_name, confidence, snapshot_path, track_id)


def insert_detections(camera_id: str, model_name: str, frame_id: int, image_path: str, names, boxes, orig_img=None) -> int:
    """Insert YOLO detection boxes into the configured PostgreSQL detections table."""
    if not enabled() or boxes is None or len(boxes) == 0:
        return 0

    rows = []
    for box in boxes:
        values = box.tolist()
        if len(values) == 7:
            x1, y1, x2, y2, track_id, confidence, class_id = values
            track_id = int(track_id)
        else:
            x1, y1, x2, y2, confidence, class_id = values[:6]
            track_id = None
        class_id = int(class_id)
        object_name = names[class_id] if isinstance(names, (list, tuple)) else names.get(class_id, str(class_id))
        rows.append(
            (
                camera_id,
                class_id,
                object_name,
                float(confidence),
                float(x1),
                float(y1),
                float(x2),
                float(y2),
                image_path or "",
                Path(model_name).name,
                frame_id,
                track_id,
            )
        )

    conn = _connect()
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO detections
            (camera_id, class_id, object_name, confidence, x1, y1, x2, y2, image_path, model_name, frame_id, track_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            rows,
        )
        _close_stale_events(cur)
        for row in rows:
            _upsert_detection_event(cur, row, orig_img)
    conn.commit()
    return len(rows)


def insert_results(camera_id: str, model_name: str, frame_id: int, results) -> int:
    """Insert detections from Ultralytics Results objects, preserving track IDs when present."""
    if not enabled():
        return 0

    inserted = 0
    for result in results:
        if result.boxes is None or len(result.boxes) == 0:
            continue
        inserted += insert_detections(
            camera_id=camera_id,
            model_name=model_name,
            frame_id=frame_id,
            image_path=str(result.path),
            names=result.names,
            boxes=result.boxes.data,
            orig_img=result.orig_img,
        )
    return inserted
