from __future__ import annotations

from collections.abc import Callable

from app.core.models import AlertRecord


class AlertRepository:
    def __init__(self, connection_factory: Callable):
        self._connection_factory = connection_factory

    def create(self, alert: AlertRecord) -> AlertRecord:
        with self._connection_factory() as connection:
            cursor = connection.execute(
                """
                INSERT INTO alerts (device_id, alert_type, severity, message, created_at, resolved_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    alert.device_id,
                    alert.alert_type,
                    alert.severity,
                    alert.message,
                    alert.created_at,
                    alert.resolved_at,
                    alert.status,
                ),
            )
            connection.commit()
        alert.id = int(cursor.lastrowid)
        return alert

    def list_recent(self, limit: int = 10) -> list[AlertRecord]:
        with self._connection_factory() as connection:
            rows = connection.execute("SELECT * FROM alerts ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [self._row_to_alert(row) for row in rows]

    def list_all(self) -> list[AlertRecord]:
        with self._connection_factory() as connection:
            rows = connection.execute("SELECT * FROM alerts ORDER BY created_at DESC").fetchall()
        return [self._row_to_alert(row) for row in rows]

    def resolve_open(self, device_id: int, alert_type: str) -> None:
        with self._connection_factory() as connection:
            connection.execute(
                """
                UPDATE alerts
                SET status = 'resolved', resolved_at = CURRENT_TIMESTAMP
                WHERE device_id = ? AND alert_type = ? AND status = 'open'
                """,
                (device_id, alert_type),
            )
            connection.commit()

    @staticmethod
    def _row_to_alert(row) -> AlertRecord:
        return AlertRecord(
            id=row["id"],
            device_id=row["device_id"],
            alert_type=row["alert_type"],
            severity=row["severity"],
            message=row["message"],
            created_at=row["created_at"],
            resolved_at=row["resolved_at"],
            status=row["status"],
        )

