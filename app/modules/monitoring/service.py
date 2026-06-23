from __future__ import annotations

import asyncio
import ipaddress
import json
from datetime import datetime, timedelta

from app.core.event_bus.bus import EventBus
from app.core.models import Device, DeviceStatus, STATUS_OFFLINE, STATUS_ONLINE, STATUS_UNKNOWN, STATUS_WARNING, utc_now
from app.core.notifications.service import NotificationService
from app.engines.alert.engine import AlertEngine
from app.engines.heartbeat.engine import HeartbeatEngine
from app.engines.http_check.engine import HttpCheckEngine
from app.engines.network_discovery.engine import NetworkDiscoveryEngine
from app.engines.port_check.engine import PortCheckEngine
from app.modules.alerts.service import AlertService
from app.modules.dashboard.service import DashboardService
from app.modules.devices.repository import DeviceRepository


DEFAULT_PORTS_BY_TYPE = {
    "Server": [22, 443],
    "Router": [80, 443],
    "Switch": [22, 443],
    "Web App": [80, 443],
    "Database": [3306, 5432],
}


class MonitoringService:
    def __init__(
        self,
        connection_factory,
        device_repository: DeviceRepository,
        dashboard_service: DashboardService,
        alert_service: AlertService,
        event_bus: EventBus,
        notifications: NotificationService,
        heartbeat_engine: HeartbeatEngine,
        port_engine: PortCheckEngine,
        http_engine: HttpCheckEngine,
        alert_engine: AlertEngine,
        discovery_engine: NetworkDiscoveryEngine,
        settings_service,
    ) -> None:
        self._connection_factory = connection_factory
        self._device_repository = device_repository
        self._dashboard_service = dashboard_service
        self._alert_service = alert_service
        self._event_bus = event_bus
        self._notifications = notifications
        self._heartbeat_engine = heartbeat_engine
        self._port_engine = port_engine
        self._http_engine = http_engine
        self._alert_engine = alert_engine
        self._discovery_engine = discovery_engine
        self._settings_service = settings_service

    async def poll_cycle(self):
        devices = [device for device in self._device_repository.list_devices() if device.enabled]
        await asyncio.gather(*(self._poll_device(device) for device in devices))
        summary = self._dashboard_service.build_summary()
        self._event_bus.publish("monitoring.cycle_completed", summary)
        return summary

    async def discover_devices(self, subnet: str):
        try:
            ipaddress.ip_network(subnet, strict=False)
        except ValueError as exc:
            raise ValueError("A valid subnet such as 192.168.1.0/24 is required.") from exc
        timeout_ms = int(self._settings_service.get("ping_timeout_ms"))
        return await self._discovery_engine.discover(subnet, timeout_ms)

    async def _poll_device(self, device: Device) -> None:
        settings = self._settings_service.as_dict()
        previous_status = self._get_previous_status(device.id or 0)
        heartbeat = await self._heartbeat_engine.check(device.ip_address, int(settings["ping_timeout_ms"]))

        ports = device.custom_ports or DEFAULT_PORTS_BY_TYPE.get(device.device_type, [])
        port_results = await asyncio.gather(*(self._port_engine.check(device.ip_address, port) for port in ports))

        http_result = None
        if device.http_url:
            http_result = await self._http_engine.check(device.http_url, device.http_keyword)

        current_status = self._build_status(device, previous_status, heartbeat, list(port_results), http_result)
        self._save_status(device, current_status)
        alerts, resolved_types = self._alert_engine.evaluate(
            device, previous_status, current_status, heartbeat, list(port_results), http_result
        )
        for alert_type in set(resolved_types):
            self._alert_service.resolve(device.id or 0, alert_type)
        for alert in alerts:
            self._alert_service.create_alert(alert)

    def _build_status(self, device: Device, previous: DeviceStatus | None, heartbeat, port_results, http_result):
        checked_at = utc_now()
        if heartbeat.reachable:
            status = STATUS_ONLINE
        elif heartbeat.error:
            status = STATUS_OFFLINE
        else:
            status = STATUS_UNKNOWN

        if heartbeat.reachable and (
            (heartbeat.latency_ms is not None and heartbeat.latency_ms > device.latency_warning_ms)
            or any(not result.is_open for result in port_results)
            or (http_result is not None and not http_result.ok)
        ):
            status = STATUS_WARNING

        last_seen = checked_at if heartbeat.reachable else previous.last_seen if previous else None
        downtime_start = previous.downtime_start if previous else None
        downtime_end = previous.downtime_end if previous else None

        if status == STATUS_OFFLINE and (previous is None or previous.status != STATUS_OFFLINE):
            downtime_start = checked_at
            downtime_end = None
        elif previous and previous.status == STATUS_OFFLINE and status != STATUS_OFFLINE:
            downtime_end = checked_at

        return DeviceStatus(
            device_id=device.id or 0,
            status=status,
            latency_ms=heartbeat.latency_ms,
            packet_loss=heartbeat.packet_loss,
            last_seen=last_seen,
            downtime_start=downtime_start,
            downtime_end=downtime_end,
            last_error=heartbeat.error or (http_result.error if http_result and not http_result.ok else ""),
            open_ports=[result.port for result in port_results if result.is_open],
            http_status_code=http_result.status_code if http_result else None,
            http_response_ms=http_result.response_ms if http_result else None,
            http_ok=http_result.ok if http_result else None,
            checked_at=checked_at,
        )

    def _get_previous_status(self, device_id: int) -> DeviceStatus | None:
        with self._connection_factory() as connection:
            row = connection.execute("SELECT * FROM device_status WHERE device_id = ?", (device_id,)).fetchone()
        if row is None:
            return None
        return DeviceStatus(
            device_id=row["device_id"],
            status=row["status"],
            latency_ms=row["latency_ms"],
            packet_loss=row["packet_loss"],
            last_seen=row["last_seen"],
            downtime_start=row["downtime_start"],
            downtime_end=row["downtime_end"],
            last_error=row["last_error"],
            open_ports=json.loads(row["open_ports"]) if row["open_ports"] else [],
            http_status_code=row["http_status_code"],
            http_response_ms=row["http_response_ms"],
            http_ok=bool(row["http_ok"]) if row["http_ok"] is not None else None,
            checked_at=row["checked_at"],
        )

    def _save_status(self, device: Device, status: DeviceStatus) -> None:
        with self._connection_factory() as connection:
            connection.execute(
                """
                INSERT INTO device_status (
                    device_id, status, latency_ms, packet_loss, last_seen, downtime_start, downtime_end,
                    last_error, open_ports, http_status_code, http_response_ms, http_ok, checked_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(device_id) DO UPDATE SET
                    status = excluded.status,
                    latency_ms = excluded.latency_ms,
                    packet_loss = excluded.packet_loss,
                    last_seen = excluded.last_seen,
                    downtime_start = excluded.downtime_start,
                    downtime_end = excluded.downtime_end,
                    last_error = excluded.last_error,
                    open_ports = excluded.open_ports,
                    http_status_code = excluded.http_status_code,
                    http_response_ms = excluded.http_response_ms,
                    http_ok = excluded.http_ok,
                    checked_at = excluded.checked_at
                """,
                (
                    status.device_id,
                    status.status,
                    status.latency_ms,
                    status.packet_loss,
                    status.last_seen,
                    status.downtime_start,
                    status.downtime_end,
                    status.last_error,
                    json.dumps(status.open_ports),
                    status.http_status_code,
                    status.http_response_ms,
                    int(status.http_ok) if status.http_ok is not None else None,
                    status.checked_at,
                ),
            )
            connection.execute(
                """
                INSERT INTO monitoring_runs (
                    device_id, checked_at, status, latency_ms, packet_loss, http_status_code, http_response_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    status.device_id,
                    status.checked_at,
                    status.status,
                    status.latency_ms,
                    status.packet_loss,
                    status.http_status_code,
                    status.http_response_ms,
                ),
            )
            connection.commit()

