from __future__ import annotations

from app.core.models import AlertRecord, Device, DeviceStatus, HeartbeatResult, HttpCheckResult, PortCheckResult


class AlertEngine:
    def evaluate(
        self,
        device: Device,
        previous_status: DeviceStatus | None,
        current_status: DeviceStatus,
        heartbeat: HeartbeatResult,
        port_results: list[PortCheckResult],
        http_result: HttpCheckResult | None,
    ) -> tuple[list[AlertRecord], list[str]]:
        alerts: list[AlertRecord] = []
        resolved_types: list[str] = []

        previous_value = previous_status.status if previous_status else None
        if current_status.status == "Offline" and previous_value != "Offline":
            alerts.append(
                AlertRecord(
                    device_id=device.id or 0,
                    alert_type="offline",
                    severity="critical",
                    message=f"{device.name} is offline",
                )
            )
        elif previous_value == "Offline" and current_status.status != "Offline":
            resolved_types.append("offline")

        if heartbeat.latency_ms and heartbeat.latency_ms > device.latency_warning_ms:
            alerts.append(
                AlertRecord(
                    device_id=device.id or 0,
                    alert_type="latency",
                    severity="warning",
                    message=f"{device.name} latency is {heartbeat.latency_ms:.0f} ms",
                )
            )
        else:
            resolved_types.append("latency")

        if any(not result.is_open for result in port_results):
            failed_ports = ", ".join(str(result.port) for result in port_results if not result.is_open)
            alerts.append(
                AlertRecord(
                    device_id=device.id or 0,
                    alert_type="port",
                    severity="warning",
                    message=f"{device.name} has closed ports: {failed_ports}",
                )
            )
        else:
            resolved_types.append("port")

        if http_result is not None and not http_result.ok:
            alerts.append(
                AlertRecord(
                    device_id=device.id or 0,
                    alert_type="http",
                    severity="warning",
                    message=f"{device.name} HTTP check failed",
                )
            )
        elif http_result is not None:
            resolved_types.append("http")

        return alerts, resolved_types

