SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    ip_address TEXT NOT NULL UNIQUE,
    device_type TEXT NOT NULL,
    location TEXT NOT NULL DEFAULT '',
    monitoring_profile TEXT NOT NULL DEFAULT 'standard',
    enabled INTEGER NOT NULL DEFAULT 1,
    custom_ports TEXT NOT NULL DEFAULT '',
    http_url TEXT NOT NULL DEFAULT '',
    http_keyword TEXT NOT NULL DEFAULT '',
    latency_warning_ms INTEGER NOT NULL DEFAULT 250,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS device_status (
    device_id INTEGER PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'Unknown',
    latency_ms REAL,
    packet_loss REAL,
    last_seen TEXT,
    downtime_start TEXT,
    downtime_end TEXT,
    last_error TEXT NOT NULL DEFAULT '',
    open_ports TEXT NOT NULL DEFAULT '',
    http_status_code INTEGER,
    http_response_ms REAL,
    http_ok INTEGER,
    checked_at TEXT NOT NULL,
    FOREIGN KEY(device_id) REFERENCES devices(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL,
    resolved_at TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    FOREIGN KEY(device_id) REFERENCES devices(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS monitoring_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL,
    checked_at TEXT NOT NULL,
    status TEXT NOT NULL,
    latency_ms REAL,
    packet_loss REAL,
    http_status_code INTEGER,
    http_response_ms REAL,
    FOREIGN KEY(device_id) REFERENCES devices(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

