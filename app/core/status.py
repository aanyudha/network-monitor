from __future__ import annotations

from app.core.models import Device, DeviceStatus, STATUS_OFFLINE, STATUS_ONLINE, STATUS_UNKNOWN, STATUS_WARNING


STATUS_META = {
    STATUS_ONLINE: {"color": "#33c27f", "dot": "#33c27f", "label": STATUS_ONLINE},
    STATUS_WARNING: {"color": "#ffbf47", "dot": "#ffbf47", "label": STATUS_WARNING},
    STATUS_OFFLINE: {"color": "#ff6577", "dot": "#ff6577", "label": STATUS_OFFLINE},
    STATUS_UNKNOWN: {"color": "#7d8597", "dot": "#2f3542", "label": STATUS_UNKNOWN},
}


def status_meta(status: str, enabled: bool = True) -> dict[str, str]:
    if not enabled:
        disabled = dict(STATUS_META[STATUS_UNKNOWN])
        disabled["label"] = "Disabled"
        return disabled
    return STATUS_META.get(status, STATUS_META[STATUS_UNKNOWN])


def build_status_snapshot(
    device: Device,
    previous: DeviceStatus | None,
    heartbeat,
    port_results,
    http_result,
    retry_count: int,
    checked_at: str,
) -> DeviceStatus:
    if not device.enabled:
        return DeviceStatus(device_id=device.id or 0, status=STATUS_UNKNOWN, checked_at=checked_at)

    previous_failures = previous.consecutive_failures if previous else 0
    consecutive_failures = 0 if heartbeat.reachable else previous_failures + 1

    if heartbeat.reachable:
        status = STATUS_ONLINE
    elif consecutive_failures > retry_count:
        status = STATUS_OFFLINE
    else:
        status = STATUS_WARNING

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
        consecutive_failures=consecutive_failures,
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
