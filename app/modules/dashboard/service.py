from __future__ import annotations

import json

from app.core.models import DashboardSummary
from app.modules.alerts.service import AlertService


class DashboardService:
    def __init__(self, connection_factory, alert_service: AlertService) -> None:
        self._connection_factory = connection_factory
        self._alert_service = alert_service

    def build_summary(self) -> DashboardSummary:
        with self._connection_factory() as connection:
            device_rows = connection.execute(
                """
                SELECT d.id, d.name, d.ip_address, d.device_type, d.location, d.enabled,
                       s.status, s.latency_ms, s.last_seen, s.last_error, s.open_ports,
                       s.http_status_code, s.checked_at
                FROM devices d
                LEFT JOIN device_status s ON s.device_id = d.id
                ORDER BY d.name
                """
            ).fetchall()

        summary = DashboardSummary()
        summary.total_devices = len(device_rows)
        latency_values = []

        for row in device_rows:
            status = "Unknown" if not bool(row["enabled"]) else row["status"] or "Unknown"
            if status == "Online":
                summary.online_devices += 1
            elif status == "Offline":
                summary.offline_devices += 1
            elif status == "Warning":
                summary.warning_devices += 1
            else:
                summary.unknown_devices += 1

            if row["latency_ms"] is not None:
                latency_values.append(float(row["latency_ms"]))

            summary.status_rows.append(
                {
                    "device_id": row["id"],
                    "name": row["name"],
                    "ip_address": row["ip_address"],
                    "device_type": row["device_type"],
                    "location": row["location"],
                    "enabled": bool(row["enabled"]),
                    "status": status,
                    "latency_ms": row["latency_ms"],
                    "last_seen": row["last_seen"] or "-",
                    "last_error": row["last_error"] or "",
                    "open_ports": ", ".join(str(value) for value in json.loads(row["open_ports"] or "[]")),
                    "http_status_code": row["http_status_code"] or "-",
                    "checked_at": row["checked_at"] or "-",
                }
            )

        summary.average_latency_ms = round(sum(latency_values) / len(latency_values), 2) if latency_values else 0.0
        if summary.total_devices:
            healthy = summary.online_devices + (summary.warning_devices * 0.5)
            summary.network_health_percent = round((healthy / summary.total_devices) * 100, 1)
        summary.recent_alerts = self._alert_service.recent_alerts(8)
        return summary
