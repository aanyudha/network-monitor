from __future__ import annotations

import json
import sqlite3


DEFAULT_SETTINGS = {
    "polling_interval_seconds": 15,
    "ping_timeout_ms": 1200,
    "retry_count": 1,
    "theme_mode": "dark",
    "database_path": "data/heisenberg_monitor.db",
}


class SettingsService:
    def __init__(self, connection_factory) -> None:
        self._connection_factory = connection_factory
        self.ensure_defaults()

    def ensure_defaults(self) -> None:
        with self._connection_factory() as connection:
            for key, value in DEFAULT_SETTINGS.items():
                connection.execute(
                    "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                    (key, json.dumps(value)),
                )
            connection.commit()

    def get(self, key: str):
        with self._connection_factory() as connection:
            row = connection.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        if row is None:
            return DEFAULT_SETTINGS.get(key)
        return json.loads(row["value"])

    def set(self, key: str, value) -> None:
        with self._connection_factory() as connection:
            connection.execute(
                """
                INSERT INTO settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, json.dumps(value)),
            )
            connection.commit()

    def as_dict(self) -> dict[str, object]:
        with self._connection_factory() as connection:
            rows = connection.execute("SELECT key, value FROM settings").fetchall()
        settings = {row["key"]: json.loads(row["value"]) for row in rows}
        merged = dict(DEFAULT_SETTINGS)
        merged.update(settings)
        return merged
