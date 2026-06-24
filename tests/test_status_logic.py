from __future__ import annotations

from app.core.models import Device, DeviceStatus, HeartbeatResult, PortCheckResult
from app.core.status import build_status_snapshot, status_meta


def test_status_light_mapping_uses_expected_labels() -> None:
    assert status_meta("Online")["label"] == "Online"
    assert status_meta("Warning")["label"] == "Warning"
    assert status_meta("Offline")["label"] == "Offline"
    assert status_meta("Unknown", enabled=False)["label"] == "Disabled"


def test_status_logic_requires_retry_count_before_offline() -> None:
    device = Device(id=1, name="Gateway", ip_address="192.0.2.1", device_type="Router")
    previous = DeviceStatus(device_id=1, status="Warning", consecutive_failures=1)
    heartbeat = HeartbeatResult(reachable=False, latency_ms=None, packet_loss=100.0, error="timeout")

    current = build_status_snapshot(
        device=device,
        previous=previous,
        heartbeat=heartbeat,
        port_results=[],
        http_result=None,
        retry_count=2,
        checked_at="2026-06-24T00:00:00+00:00",
    )

    assert current.status == "Warning"
    assert current.consecutive_failures == 2


def test_status_logic_marks_warning_for_port_failures() -> None:
    device = Device(id=2, name="Web", ip_address="192.0.2.20", device_type="Web App")
    heartbeat = HeartbeatResult(reachable=True, latency_ms=10.0, packet_loss=0.0, error="")

    current = build_status_snapshot(
        device=device,
        previous=None,
        heartbeat=heartbeat,
        port_results=[PortCheckResult(port=443, is_open=False)],
        http_result=None,
        retry_count=1,
        checked_at="2026-06-24T00:00:00+00:00",
    )

    assert current.status == "Warning"
