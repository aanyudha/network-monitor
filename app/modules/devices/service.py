from __future__ import annotations

import ipaddress
from urllib.parse import urlparse

from app.core.models import DEVICE_TYPES, Device, DiscoveryResult, utc_now
from app.modules.devices.repository import DeviceRepository


class DeviceService:
    def __init__(self, repository: DeviceRepository) -> None:
        self._repository = repository

    def list_devices(self) -> list[Device]:
        return self._repository.list_devices()

    def get_device(self, device_id: int) -> Device | None:
        return self._repository.get_device(device_id)

    def create_device(self, device: Device) -> Device:
        self.validate_device(device)
        existing = self._repository.get_by_ip(device.ip_address)
        if existing:
            raise ValueError("A device with this IP address already exists.")
        timestamp = utc_now()
        device.created_at = timestamp
        device.updated_at = timestamp
        return self._repository.create(device)

    def update_device(self, device: Device) -> Device:
        self.validate_device(device)
        existing = self._repository.get_by_ip(device.ip_address)
        if existing and existing.id != device.id:
            raise ValueError("A device with this IP address already exists.")
        device.updated_at = utc_now()
        return self._repository.update(device)

    def merge_discovery_result(
        self,
        result: DiscoveryResult,
        selected_type: str | None = None,
        lock_type: bool = False,
        force_type_override: bool = False,
    ) -> tuple[Device, str]:
        detected_type = selected_type or result.device_type or "Unknown"
        timestamp = utc_now()
        existing = self._repository.get_by_ip(result.ip_address)
        if existing is None:
            created = Device(
                name=result.hostname or f"Discovered {result.ip_address}",
                ip_address=result.ip_address,
                device_type=detected_type,
                device_type_confidence=result.device_type_confidence,
                discovery_notes=result.discovery_notes,
                device_type_locked=lock_type,
                created_at=timestamp,
                updated_at=timestamp,
            )
            return self.create_device(created), "created"

        existing.name = existing.name or result.hostname or existing.name
        if result.hostname and existing.name.startswith("Discovered "):
            existing.name = result.hostname

        should_update_type = force_type_override or not existing.device_type_locked
        if should_update_type:
            existing.device_type = detected_type
            existing.device_type_confidence = result.device_type_confidence
            existing.discovery_notes = result.discovery_notes
        elif not existing.discovery_notes:
            existing.discovery_notes = result.discovery_notes

        if lock_type:
            existing.device_type_locked = True

        existing.updated_at = timestamp
        return self.update_device(existing), "updated"

    def delete_device(self, device_id: int) -> None:
        self._repository.delete(device_id)

    def validate_device(self, device: Device) -> None:
        if not device.name.strip():
            raise ValueError("Device name is required.")
        try:
            ipaddress.ip_address(device.ip_address)
        except ValueError as exc:
            raise ValueError("A valid IP address is required.") from exc
        if device.device_type not in DEVICE_TYPES:
            raise ValueError("Unsupported device type.")
        if not 0 <= device.device_type_confidence <= 100:
            raise ValueError("Device type confidence must be between 0 and 100.")
        if device.http_url:
            parsed = urlparse(device.http_url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError("HTTP URL must be a valid http:// or https:// URL.")
        for port in device.custom_ports:
            if port < 1 or port > 65535:
                raise ValueError("Ports must be between 1 and 65535.")
