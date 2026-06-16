CREATE TABLE IF NOT EXISTS detections (
    id BIGSERIAL PRIMARY KEY,
    camera_id VARCHAR(100) NOT NULL,
    object_name VARCHAR(100) NOT NULL,
    confidence NUMERIC(5,4) NOT NULL,
    x1 REAL NOT NULL,
    y1 REAL NOT NULL,
    x2 REAL NOT NULL,
    y2 REAL NOT NULL,
    image_path TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    class_id INTEGER NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    frame_id BIGINT NOT NULL,
    track_id INTEGER
);

CREATE TABLE IF NOT EXISTS detection_events (
    id BIGSERIAL PRIMARY KEY,
    camera_id VARCHAR(100) NOT NULL,
    class_id INTEGER NOT NULL,
    object_name VARCHAR(100) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    track_id INTEGER,
    start_time TIMESTAMP NOT NULL DEFAULT NOW(),
    end_time TIMESTAMP NOT NULL DEFAULT NOW(),
    first_frame_id BIGINT NOT NULL,
    last_frame_id BIGINT NOT NULL,
    detection_count INTEGER NOT NULL DEFAULT 1,
    max_confidence NUMERIC(5,4) NOT NULL,
    last_confidence NUMERIC(5,4) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    snapshot_path TEXT
);

CREATE TABLE IF NOT EXISTS alerts (
    id BIGSERIAL PRIMARY KEY,
    camera_id VARCHAR(100) NOT NULL,
    alert_type VARCHAR(100) NOT NULL,
    object_name VARCHAR(100) NOT NULL,
    event_id BIGINT REFERENCES detection_events(id),
    message TEXT NOT NULL,
    confidence NUMERIC(5,4),
    snapshot_path TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'new',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    track_id INTEGER
);

CREATE TABLE IF NOT EXISTS alert_rules (
    id BIGSERIAL PRIMARY KEY,
    camera_id VARCHAR(100) NOT NULL DEFAULT '*',
    object_name VARCHAR(100) NOT NULL,
    alert_type VARCHAR(100) NOT NULL,
    min_confidence NUMERIC(5,4) NOT NULL DEFAULT 0.5000,
    min_duration_seconds INTEGER NOT NULL DEFAULT 0,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    message_template TEXT NOT NULL DEFAULT '{object_name} detected on {camera_id}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(camera_id, object_name, alert_type)
);

INSERT INTO alert_rules (camera_id, object_name, alert_type, min_confidence, min_duration_seconds, enabled, message_template)
VALUES ('*', 'person', 'person_detected', 0.5000, 0, TRUE, '{object_name} detected on {camera_id}')
ON CONFLICT (camera_id, object_name, alert_type) DO NOTHING;

CREATE INDEX IF NOT EXISTS idx_detections_created_at ON detections(created_at);
CREATE INDEX IF NOT EXISTS idx_detections_camera_time ON detections(camera_id, created_at);
CREATE INDEX IF NOT EXISTS idx_detections_object_time ON detections(object_name, created_at);
CREATE INDEX IF NOT EXISTS idx_detections_frame_id ON detections(frame_id);

CREATE INDEX IF NOT EXISTS idx_detection_events_camera_time ON detection_events(camera_id, start_time DESC);
CREATE INDEX IF NOT EXISTS idx_detection_events_object_status ON detection_events(object_name, status);
CREATE INDEX IF NOT EXISTS idx_detection_events_status_time ON detection_events(status, end_time DESC);

CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
CREATE UNIQUE INDEX IF NOT EXISTS idx_alerts_event_type_unique
ON alerts(event_id, alert_type)
WHERE event_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_alert_rules_enabled_object
ON alert_rules(enabled, object_name, camera_id);

CREATE OR REPLACE VIEW active_detection_events AS
SELECT id,
       camera_id,
       track_id,
       object_name,
       model_name,
       detection_count,
       max_confidence,
       last_confidence,
       snapshot_path,
       start_time,
       end_time,
       EXTRACT(EPOCH FROM (NOW() - start_time))::INTEGER AS duration_seconds
FROM detection_events
WHERE status = 'active'
ORDER BY end_time DESC;

CREATE OR REPLACE VIEW detection_summary_last_hour AS
SELECT camera_id,
       object_name,
       COUNT(*) AS total_detections,
       MAX(confidence) AS max_confidence,
       MIN(created_at) AS first_seen,
       MAX(created_at) AS last_seen
FROM detections
WHERE created_at >= NOW() - INTERVAL '1 hour'
GROUP BY camera_id, object_name
ORDER BY total_detections DESC;

CREATE OR REPLACE VIEW webcam_summary_last_hour AS
SELECT camera_id,
       object_name,
       total_detections,
       max_confidence,
       first_seen,
       last_seen
FROM detection_summary_last_hour
WHERE camera_id = 'webcam_01';

CREATE OR REPLACE VIEW new_alerts AS
SELECT *
FROM alerts
WHERE status = 'new'
ORDER BY created_at DESC;
