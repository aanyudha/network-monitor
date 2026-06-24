from __future__ import annotations

from app.core.event_bus.bus import EventBus
from app.core.models import DiscoveryResult
from app.modules.discovery.service import DiscoveryService


class DiscoveryActions:
    def __init__(self, discovery_service: DiscoveryService, event_bus: EventBus) -> None:
        self._discovery_service = discovery_service
        self._event_bus = event_bus

    def review(self, results: list[DiscoveryResult]) -> list[DiscoveryResult]:
        return self._discovery_service.annotate_results(results)

    def import_selected(self, selections: list[dict[str, object]]) -> dict[str, int]:
        summary = self._discovery_service.import_selected(selections)
        self._event_bus.publish("device.changed", {"action": "discovery_imported", **summary})
        return summary
