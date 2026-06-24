from __future__ import annotations

from app.core.models import DiscoveryResult
from app.modules.devices.repository import DeviceRepository
from app.modules.devices.service import DeviceService


class DiscoveryService:
    def __init__(self, device_repository: DeviceRepository, device_service: DeviceService) -> None:
        self._device_repository = device_repository
        self._device_service = device_service

    def annotate_results(self, results: list[DiscoveryResult]) -> list[DiscoveryResult]:
        annotated: list[DiscoveryResult] = []
        for result in results:
            existing = self._device_repository.get_by_ip(result.ip_address)
            status = "Existing device" if existing else "New device"
            annotated.append(
                DiscoveryResult(
                    ip_address=result.ip_address,
                    hostname=result.hostname,
                    reachable=result.reachable,
                    device_type=result.device_type,
                    device_type_confidence=result.device_type_confidence,
                    discovery_notes=result.discovery_notes,
                    open_ports=list(result.open_ports),
                    http_title=result.http_title,
                    http_status_code=result.http_status_code,
                    vendor_name=result.vendor_name,
                    status=status,
                    is_existing_device=existing is not None,
                )
            )
        return annotated

    def import_selected(self, selections: list[dict[str, object]]) -> dict[str, int]:
        created = 0
        updated = 0
        skipped = 0

        for selection in selections:
            result = selection["result"]
            if not isinstance(result, DiscoveryResult):
                skipped += 1
                continue
            selected_type = str(selection.get("selected_type") or result.device_type or "Unknown")
            lock_type = bool(selection.get("lock_type", False))
            _, action = self._device_service.merge_discovery_result(
                result=result,
                selected_type=selected_type,
                lock_type=lock_type,
            )
            if action == "created":
                created += 1
            elif action == "updated":
                updated += 1
            else:
                skipped += 1

        return {"created": created, "updated": updated, "skipped": skipped}
