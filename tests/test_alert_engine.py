from __future__ import annotations

from app.core.models import Device, DeviceStatus, HeartbeatResult
from app.engines.alert.engine import AlertEngine


def test_offline_transition_creates_alert() -> None:
    engine = AlertEngine()
    device = Device(id=1, name="DB", ip_address="192.0.2.50")
    previous = DeviceStatus(device_id=1, status="Online")
    current = DeviceStatus(device_id=1, status="Offline")
    heartbeat = HeartbeatResult(reachable=False, latency_ms=None, packet_loss=100.0, error="timeout")

    alerts, resolved = engine.evaluate(device, previous, current, heartbeat, [], None)

    assert any(alert.alert_type == "offline" for alert in alerts)
    assert "latency" in resolved


def test_recovery_marks_offline_resolved() -> None:
    engine = AlertEngine()
    device = Device(id=1, name="DB", ip_address="192.0.2.50")
    previous = DeviceStatus(device_id=1, status="Offline")
    current = DeviceStatus(device_id=1, status="Online")
    heartbeat = HeartbeatResult(reachable=True, latency_ms=10.0, packet_loss=0.0, error="")

    alerts, resolved = engine.evaluate(device, previous, current, heartbeat, [], None)

    assert alerts == []
    assert "offline" in resolved

