from __future__ import annotations

from app.core.models import Device
from app.core.event_bus.bus import EventBus
from app.modules.devices.service import DeviceService


class DeviceActions:
    def __init__(self, device_service: DeviceService, event_bus: EventBus) -> None:
        self._device_service = device_service
        self._event_bus = event_bus

    def create(self, device: Device) -> Device:
        created = self._device_service.create_device(device)
        self._event_bus.publish("device.changed", {"action": "created", "device_id": created.id})
        return created

    def update(self, device: Device) -> Device:
        updated = self._device_service.update_device(device)
        self._event_bus.publish("device.changed", {"action": "updated", "device_id": updated.id})
        return updated

    def delete(self, device_id: int) -> None:
        self._device_service.delete_device(device_id)
        self._event_bus.publish("device.changed", {"action": "deleted", "device_id": device_id})

