from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


DEVICE_TYPES = [
    "PC",
    "Server",
    "Router",
    "Switch",
    "AP",
    "Printer",
    "CCTV",
    "NVR",
    "Web App",
    "Database",
    "Other",
]

STATUS_ONLINE = "Online"
STATUS_OFFLINE = "Offline"
STATUS_WARNING = "Warning"
STATUS_UNKNOWN = "Unknown"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(slots=True)
class Device:
    name: str
    ip_address: str
    device_type: str = "Other"
    location: str = ""
    monitoring_profile: str = "standard"
    enabled: bool = True
    custom_ports: list[int] = field(default_factory=list)
    http_url: str = ""
    http_keyword: str = ""
    latency_warning_ms: int = 250
    id: int | None = None
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)


@dataclass(slots=True)
class DeviceStatus:
    device_id: int
    status: str = STATUS_UNKNOWN
    latency_ms: float | None = None
    packet_loss: float | None = None
    last_seen: str | None = None
    downtime_start: str | None = None
    downtime_end: str | None = None
    last_error: str = ""
    open_ports: list[int] = field(default_factory=list)
    http_status_code: int | None = None
    http_response_ms: float | None = None
    http_ok: bool | None = None
    checked_at: str = field(default_factory=utc_now)


@dataclass(slots=True)
class HeartbeatResult:
    reachable: bool
    latency_ms: float | None
    packet_loss: float | None
    error: str = ""


@dataclass(slots=True)
class PortCheckResult:
    port: int
    is_open: bool
    error: str = ""


@dataclass(slots=True)
class HttpCheckResult:
    ok: bool
    status_code: int | None
    response_ms: float | None
    matched_keyword: bool = True
    error: str = ""


@dataclass(slots=True)
class AlertRecord:
    device_id: int
    alert_type: str
    severity: str
    message: str
    id: int | None = None
    created_at: str = field(default_factory=utc_now)
    resolved_at: str | None = None
    status: str = "open"


@dataclass(slots=True)
class DashboardSummary:
    total_devices: int = 0
    online_devices: int = 0
    offline_devices: int = 0
    warning_devices: int = 0
    unknown_devices: int = 0
    average_latency_ms: float = 0.0
    network_health_percent: float = 0.0
    recent_alerts: list[AlertRecord] = field(default_factory=list)
    status_rows: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class DiscoveryResult:
    ip_address: str
    hostname: str = ""
    reachable: bool = True
