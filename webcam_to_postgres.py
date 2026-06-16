from __future__ import annotations

import os
from pathlib import Path

import cv2
import psycopg2
from ultralytics import YOLO


MODEL_PATH = os.getenv("YOLO_MODEL", "yolo11n.pt")
CAMERA_SOURCE = os.getenv("CAMERA_SOURCE", "0")
CAMERA_ID = os.getenv("CAMERA_ID", "webcam_01")
SNAPSHOT_DIR = Path(os.getenv("SNAPSHOT_DIR", "snapshots"))
SAVE_SNAPSHOTS = os.getenv("SAVE_SNAPSHOTS", "1") == "1"
CONFIDENCE = float(os.getenv("YOLO_CONF", "0.25"))

DB_CONFIG = {
    "dbname": os.getenv("PGDATABASE", "camera_ai"),
    "user": os.getenv("PGUSER", "postgres"),
    "password": os.getenv("PGPASSWORD", ""),
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", "5432")),
}


def camera_source(value: str) -> int | str:
    return int(value) if value.isdigit() else value


def open_capture(source: int | str) -> cv2.VideoCapture:
    if os.name == "nt" and isinstance(source, int):
        cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)
    else:
        cap = cv2.VideoCapture(source)
    return cap


def insert_detection(conn, row: tuple) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO detections
            (camera_id, class_id, object_name, confidence, x1, y1, x2, y2, image_path, model_name, frame_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            row,
        )


def main() -> None:
    if SAVE_SNAPSHOTS:
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    model = YOLO(MODEL_PATH)
    conn = psycopg2.connect(**DB_CONFIG)
    cap = open_capture(camera_source(CAMERA_SOURCE))

    if not cap.isOpened():
        raise RuntimeError(
            f"Cannot open camera source: {CAMERA_SOURCE}. Close other apps using the webcam or try CAMERA_SOURCE=1."
        )

    frame_id = 0

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                raise RuntimeError(
                    "Cannot read frame from webcam. Close other camera apps, then try again. "
                    "If it still fails, run with CAMERA_SOURCE=1."
                )

            results = model(frame, conf=CONFIDENCE, verbose=False)
            image_path = ""

            if SAVE_SNAPSHOTS and any(len(r.boxes) for r in results):
                image_path = str(SNAPSHOT_DIR / f"{CAMERA_ID}_{frame_id:08d}.jpg")
                cv2.imwrite(image_path, frame)

            for result in results:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    object_name = model.names[class_id]
                    confidence = float(box.conf[0])
                    x1, y1, x2, y2 = map(float, box.xyxy[0])

                    insert_detection(
                        conn,
                        (
                            CAMERA_ID,
                            class_id,
                            object_name,
                            confidence,
                            x1,
                            y1,
                            x2,
                            y2,
                            image_path,
                            Path(MODEL_PATH).name,
                            frame_id,
                        ),
                    )

            conn.commit()

            annotated = results[0].plot()
            cv2.imshow("YOLO webcam", annotated)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

            frame_id += 1
    finally:
        cap.release()
        cv2.destroyAllWindows()
        conn.close()


if __name__ == "__main__":
    main()
