from __future__ import annotations

from pathlib import Path

from app.core.models import Device


def test_export_availability_csv(connection_factory, device_service, reporting_service, tmp_path: Path) -> None:
    created = device_service.create_device(Device(name="App", ip_address="192.0.2.25"))
    with connection_factory() as connection:
        connection.execute(
            """
            INSERT INTO monitoring_runs (
                device_id, checked_at, status, latency_ms, packet_loss, http_status_code, http_response_ms
            ) VALUES (?, CURRENT_TIMESTAMP, 'Online', 12.5, 0, 200, 120.0)
            """,
            (created.id,),
        )
        connection.execute(
            """
            INSERT INTO monitoring_runs (
                device_id, checked_at, status, latency_ms, packet_loss, http_status_code, http_response_ms
            ) VALUES (?, CURRENT_TIMESTAMP, 'Offline', NULL, 100, NULL, NULL)
            """,
            (created.id,),
        )
        connection.commit()

    destination = tmp_path / "availability.csv"
    exported = reporting_service.export_availability_csv(destination, days=30)

    content = exported.read_text(encoding="utf-8")
    assert "availability_percent" in content
    assert "192.0.2.25" in content

