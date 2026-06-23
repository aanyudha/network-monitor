from __future__ import annotations

from app.core.models import Device
from app.modules.devices.service import DeviceService


def seed_example_devices(device_service: DeviceService) -> None:
    if device_service.list_devices():
        return

    samples = [
        Device(name="Gateway", ip_address="192.168.1.1", device_type="Router", custom_ports=[80, 443]),
        Device(name="App Server", ip_address="192.168.1.10", device_type="Server", custom_ports=[22, 443]),
        Device(
            name="Example Web",
            ip_address="198.51.100.10",
            device_type="Web App",
            http_url="https://example.com",
        ),
    ]

    for sample in samples:
        device_service.create_device(sample)

