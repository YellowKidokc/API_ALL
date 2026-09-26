-- 04_artifact_manifest_routes.sql
-- Adds artifact manifests and station routing to file-intelligence.station.

CREATE TABLE IF NOT EXISTS artifact_manifests (
    artifact_id      TEXT PRIMARY KEY,
    file_id          INT REFERENCES files(file_id) ON DELETE SET NULL,
    sha256           TEXT,
    manifest         JSONB NOT NULL,
    created_at       TIMESTAMP DEFAULT NOW(),
    updated_at       TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS artifact_routes (
    route_id         SERIAL PRIMARY KEY,
    artifact_id      TEXT REFERENCES artifact_manifests(artifact_id) ON DELETE CASCADE,
    station_name     TEXT NOT NULL,
    route_reason     TEXT,
    confidence       FLOAT,
    status           TEXT DEFAULT 'pending', -- pending, running, complete, skipped, failed
    result_path      TEXT,
    created_at       TIMESTAMP DEFAULT NOW(),
    updated_at       TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS preference_events (
    event_id         SERIAL PRIMARY KEY,
    model_name       TEXT DEFAULT 'portable_preference_kernel',
    features         JSONB NOT NULL,
    action           TEXT NOT NULL,
    reward           FLOAT NOT NULL,
    model_path       TEXT,
    created_at       TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_artifact_manifests_sha256 ON artifact_manifests(sha256);
CREATE INDEX IF NOT EXISTS idx_artifact_routes_artifact ON artifact_routes(artifact_id);
CREATE INDEX IF NOT EXISTS idx_artifact_routes_station ON artifact_routes(station_name);
CREATE INDEX IF NOT EXISTS idx_artifact_routes_status ON artifact_routes(status);
CREATE INDEX IF NOT EXISTS idx_preference_events_action ON preference_events(action);
