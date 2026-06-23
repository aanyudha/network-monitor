from __future__ import annotations

import asyncio

from app.engines.heartbeat.engine import HeartbeatEngine


def test_heartbeat_output_parsers() -> None:
    windows_output = "Reply from 192.0.2.1: bytes=32 time=12ms TTL=64\n    Lost = 0 (0% loss)"
    linux_output = "64 bytes from 192.0.2.1: icmp_seq=1 ttl=64 time=8.2 ms\n1 packets transmitted, 1 received, 0% packet loss"

    assert HeartbeatEngine.parse_latency(windows_output) == 12.0
    assert HeartbeatEngine.parse_latency(linux_output) == 8.2
    assert HeartbeatEngine.parse_packet_loss(linux_output) == 0.0


def test_invalid_subnet_is_rejected(monitoring_service) -> None:
    try:
        asyncio.run(monitoring_service.discover_devices("not-a-subnet"))
    except ValueError as exc:
        assert "valid subnet" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid subnet")
