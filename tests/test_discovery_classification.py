from __future__ import annotations

from app.core.models import Device, DiscoveryFingerprint, DiscoveryResult
from app.engines.network_discovery.classification import DiscoveryClassificationEngine


def test_classification_rules_identify_printer() -> None:
    engine = DiscoveryClassificationEngine()

    classification = engine.classify(
        DiscoveryFingerprint(
            ip_address="192.0.2.40",
            hostname="hp-laserjet",
            open_ports=[80, 9100],
            http_title="HP LaserJet Admin",
        )
    )

    assert classification.device_type == "Printer"
    assert classification.confidence >= 70
    assert "printer" in classification.notes.lower()


def test_classification_rules_identify_router_from_gateway_signal() -> None:
    engine = DiscoveryClassificationEngine()

    classification = engine.classify(
        DiscoveryFingerprint(
            ip_address="192.0.2.1",
            hostname="gateway-router",
            open_ports=[80, 443, 161],
            is_gateway=True,
        )
    )

    assert classification.device_type == "Router"
    assert classification.confidence >= 70


def test_manual_type_lock_is_not_overwritten(device_service) -> None:
    created = device_service.create_device(
        Device(
            name="Office Camera",
            ip_address="192.0.2.60",
            device_type="CCTV",
            device_type_confidence=95,
            discovery_notes="Manual operator override",
            device_type_locked=True,
        )
    )

    updated, action = device_service.merge_discovery_result(
        DiscoveryResult(
            ip_address="192.0.2.60",
            hostname="office-nvr",
            device_type="NVR",
            device_type_confidence=88,
            discovery_notes="RTSP and ONVIF matched recorder profile.",
        )
    )

    assert action == "updated"
    assert created.id == updated.id
    assert updated.device_type == "CCTV"
    assert updated.device_type_locked is True
