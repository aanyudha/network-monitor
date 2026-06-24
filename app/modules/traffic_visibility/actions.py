from __future__ import annotations

from pathlib import Path

from app.modules.traffic_visibility.service import TrafficVisibilityService


class ImportDnsLogAction:
    def __init__(self, traffic_service: TrafficVisibilityService) -> None:
        self._traffic_service = traffic_service

    def run(self, path: Path) -> int:
        return self._traffic_service.import_csv(path, "dns_log")


class ImportFirewallLogAction:
    def __init__(self, traffic_service: TrafficVisibilityService) -> None:
        self._traffic_service = traffic_service

    def run(self, path: Path) -> int:
        return self._traffic_service.import_csv(path, "firewall_log")


class ListDeviceTrafficAction:
    def __init__(self, traffic_service: TrafficVisibilityService) -> None:
        self._traffic_service = traffic_service

    def run(self, device_id: int, limit: int = 25) -> dict[str, object]:
        return self._traffic_service.list_device_traffic(device_id, limit)
