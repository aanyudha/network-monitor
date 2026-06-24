from __future__ import annotations

import sqlite3
from pathlib import Path

from app.core.database.schema import SCHEMA_SQL


class DatabaseManager:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(SCHEMA_SQL)
            self._run_migrations(connection)
            connection.commit()

    def _run_migrations(self, connection: sqlite3.Connection) -> None:
        self._ensure_column(connection, "devices", "device_type_confidence", "INTEGER NOT NULL DEFAULT 0")
        self._ensure_column(connection, "devices", "discovery_notes", "TEXT NOT NULL DEFAULT ''")
        self._ensure_column(connection, "devices", "device_type_locked", "INTEGER NOT NULL DEFAULT 0")
        self._ensure_column(connection, "device_status", "consecutive_failures", "INTEGER NOT NULL DEFAULT 0")

    @staticmethod
    def _ensure_column(connection: sqlite3.Connection, table: str, column: str, definition: str) -> None:
        columns = {
            row["name"] if isinstance(row, sqlite3.Row) else row[1]
            for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
        }
        if column not in columns:
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
