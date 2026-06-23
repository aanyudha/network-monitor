from __future__ import annotations

import pytest

from app.core.models import Device


def test_create_device_persists_and_lists(device_service) -> None:
    created = device_service.create_device(
        Device(
            name="Edge Router",
            ip_address="192.0.2.10",
            device_type="Router",
            custom_ports=[80, 443],
        )
    )

    devices = device_service.list_devices()

    assert created.id is not None
    assert len(devices) == 1
    assert devices[0].ip_address == "192.0.2.10"
    assert devices[0].custom_ports == [80, 443]


def test_invalid_ip_raises_validation_error(device_service) -> None:
    with pytest.raises(ValueError, match="valid IP address"):
        device_service.create_device(Device(name="Broken", ip_address="999.1.1.1"))


def test_duplicate_ip_is_rejected(device_service) -> None:
    device_service.create_device(Device(name="A", ip_address="192.0.2.11"))
    with pytest.raises(ValueError, match="already exists"):
        device_service.create_device(Device(name="B", ip_address="192.0.2.11"))

