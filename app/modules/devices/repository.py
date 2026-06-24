from __future__ import annotations

import json
from collections.abc import Callable

from app.core.models import Device


class DeviceRepository:
    def __init__(self, connection_factory: Callable):
        self._connection_factory = connection_factory

    def list_devices(self) -> list[Device]:
        with self._connection_factory() as connection:
            rows = connection.execute("SELECT * FROM devices ORDER BY name").fetchall()
        return [self._row_to_device(row) for row in rows]

    def get_device(self, device_id: int) -> Device | None:
        with self._connection_factory() as connection:
            row = connection.execute("SELECT * FROM devices WHERE id = ?", (device_id,)).fetchone()
        return self._row_to_device(row) if row else None

    def get_by_ip(self, ip_address: str) -> Device | None:
        with self._connection_factory() as connection:
            row = connection.execute("SELECT * FROM devices WHERE ip_address = ?", (ip_address,)).fetchone()
        return self._row_to_device(row) if row else None

    def create(self, device: Device) -> Device:
        with self._connection_factory() as connection:
            cursor = connection.execute(
                """
                INSERT INTO devices (
                    name, ip_address, device_type, device_type_confidence, discovery_notes, device_type_locked,
                    location, monitoring_profile, enabled, custom_ports, http_url, http_keyword,
                    latency_warning_ms, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    device.name,
                    device.ip_address,
                    device.device_type,
                    device.device_type_confidence,
                    device.discovery_notes,
                    int(device.device_type_locked),
                    device.location,
                    device.monitoring_profile,
                    int(device.enabled),
                    json.dumps(device.custom_ports),
                    device.http_url,
                    device.http_keyword,
                    device.latency_warning_ms,
                    device.created_at,
                    device.updated_at,
                ),
            )
            connection.execute(
                "INSERT INTO device_status (device_id, checked_at) VALUES (?, ?)",
                (cursor.lastrowid, device.updated_at),
            )
            connection.commit()
        created = self.get_device(int(cursor.lastrowid))
        assert created is not None
        return created

    def update(self, device: Device) -> Device:
        with self._connection_factory() as connection:
            connection.execute(
                """
                UPDATE devices SET
                    name = ?, ip_address = ?, device_type = ?, device_type_confidence = ?, discovery_notes = ?,
                    device_type_locked = ?, location = ?, monitoring_profile = ?, enabled = ?, custom_ports = ?,
                    http_url = ?, http_keyword = ?,
                    latency_warning_ms = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    device.name,
                    device.ip_address,
                    device.device_type,
                    device.device_type_confidence,
                    device.discovery_notes,
                    int(device.device_type_locked),
                    device.location,
                    device.monitoring_profile,
                    int(device.enabled),
                    json.dumps(device.custom_ports),
                    device.http_url,
                    device.http_keyword,
                    device.latency_warning_ms,
                    device.updated_at,
                    device.id,
                ),
            )
            connection.commit()
        updated = self.get_device(device.id or 0)
        assert updated is not None
        return updated

    def delete(self, device_id: int) -> None:
        with self._connection_factory() as connection:
            connection.execute("DELETE FROM devices WHERE id = ?", (device_id,))
            connection.commit()

    @staticmethod
    def _row_to_device(row) -> Device:
        return Device(
            id=row["id"],
            name=row["name"],
            ip_address=row["ip_address"],
            device_type=row["device_type"],
            device_type_confidence=row["device_type_confidence"] if "device_type_confidence" in row.keys() else 0,
            discovery_notes=row["discovery_notes"] if "discovery_notes" in row.keys() else "",
            device_type_locked=bool(row["device_type_locked"]) if "device_type_locked" in row.keys() else False,
            location=row["location"],
            monitoring_profile=row["monitoring_profile"],
            enabled=bool(row["enabled"]),
            custom_ports=json.loads(row["custom_ports"]) if row["custom_ports"] else [],
            http_url=row["http_url"],
            http_keyword=row["http_keyword"],
            latency_warning_ms=row["latency_warning_ms"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
