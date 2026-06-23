from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.engines.reporting.engine import ReportingEngine


class ReportingService:
    def __init__(self, connection_factory, reporting_engine: ReportingEngine) -> None:
        self._connection_factory = connection_factory
        self._reporting_engine = reporting_engine

    def availability_rows(self, days: int = 7) -> list[dict[str, object]]:
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        with self._connection_factory() as connection:
            rows = connection.execute(
                """
                SELECT d.name, d.ip_address,
                       COUNT(m.id) AS total_checks,
                       SUM(CASE WHEN m.status = 'Online' THEN 1 ELSE 0 END) AS online_checks,
                       SUM(CASE WHEN m.status = 'Offline' THEN 1 ELSE 0 END) AS offline_checks,
                       AVG(m.latency_ms) AS avg_latency_ms
                FROM devices d
                LEFT JOIN monitoring_runs m ON m.device_id = d.id AND m.checked_at >= ?
                GROUP BY d.id
                ORDER BY d.name
                """,
                (since,),
            ).fetchall()

        results = []
        for row in rows:
            total_checks = row["total_checks"] or 0
            online_checks = row["online_checks"] or 0
            availability = round((online_checks / total_checks) * 100, 2) if total_checks else 0.0
            results.append(
                {
                    "name": row["name"],
                    "ip_address": row["ip_address"],
                    "total_checks": total_checks,
                    "online_checks": online_checks,
                    "offline_checks": row["offline_checks"] or 0,
                    "availability_percent": availability,
                    "avg_latency_ms": round(row["avg_latency_ms"], 2) if row["avg_latency_ms"] is not None else "",
                }
            )
        return results

    def downtime_rows(self, days: int = 7) -> list[dict[str, object]]:
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        with self._connection_factory() as connection:
            rows = connection.execute(
                """
                SELECT d.name, d.ip_address, s.status, s.downtime_start, s.downtime_end
                FROM devices d
                JOIN device_status s ON s.device_id = d.id
                WHERE s.downtime_start IS NOT NULL AND s.checked_at >= ?
                ORDER BY d.name
                """,
                (since,),
            ).fetchall()
        return [dict(row) for row in rows]

    def export_availability_csv(self, destination: Path, days: int = 7) -> Path:
        rows = self.availability_rows(days)
        return self._reporting_engine.export_csv(
            destination,
            ["name", "ip_address", "total_checks", "online_checks", "offline_checks", "availability_percent", "avg_latency_ms"],
            rows,
        )
