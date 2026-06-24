from __future__ import annotations

import ipaddress
from pathlib import Path

from app.core.models import TRAFFIC_SOURCE_TYPES, TrafficObservation
from app.modules.devices.repository import DeviceRepository
from app.modules.traffic_visibility.repository import TrafficVisibilityRepository


class TrafficVisibilityService:
    def __init__(
        self,
        device_repository: DeviceRepository,
        repository: TrafficVisibilityRepository,
        engine,
    ) -> None:
        self._device_repository = device_repository
        self._repository = repository
        self._engine = engine

    def supported_source_types(self) -> list[str]:
        return list(TRAFFIC_SOURCE_TYPES)

    def import_csv(self, path: Path, source_type: str) -> int:
        observations = self._engine.import_csv(path, source_type)
        enriched = [self._enrich_observation(observation) for observation in observations]
        return self._repository.insert_many(enriched)

    def list_device_traffic(self, device_id: int, limit: int = 25) -> dict[str, object]:
        rows = self._repository.recent_for_device(device_id, limit)
        recent_domains = self._unique_values(rows, lambda item: item.domain)
        recent_public_ips = self._unique_values(rows, lambda item: item.public_ip)
        destination_ports = self._unique_values(rows, lambda item: str(item.port) if item.port is not None else None)
        last_observed = rows[0].observed_at if rows else "-"

        return {
            "rows": rows,
            "recent_domains": recent_domains,
            "recent_public_ips": recent_public_ips,
            "destination_ports": destination_ports,
            "last_observed": last_observed,
        }

    def _enrich_observation(self, observation: TrafficObservation) -> TrafficObservation:
        device = self._device_repository.get_by_ip(observation.source_ip)
        observation.device_id = device.id if device else None
        observation.public_ip = self._extract_public_ip(observation.destination_ip)
        return observation

    @staticmethod
    def _extract_public_ip(destination_ip: str | None) -> str | None:
        if not destination_ip:
            return None
        try:
            parsed = ipaddress.ip_address(destination_ip)
        except ValueError:
            return None
        return destination_ip if parsed.is_global else None

    @staticmethod
    def _unique_values(rows: list[TrafficObservation], selector) -> list[str]:
        seen: set[str] = set()
        values: list[str] = []
        for row in rows:
            value = selector(row)
            if value and value not in seen:
                seen.add(value)
                values.append(value)
        return values[:10]
