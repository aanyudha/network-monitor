from __future__ import annotations

from pathlib import Path

import pytest

from app.core.models import Device


def test_csv_traffic_import_and_source_ip_mapping(
    device_service,
    traffic_visibility_service,
    tmp_path: Path,
) -> None:
    created = device_service.create_device(Device(name="Workstation", ip_address="192.0.2.90", device_type="PC"))
    csv_path = tmp_path / "dns.csv"
    csv_path.write_text(
        "timestamp,source_ip,destination_ip,domain,protocol,port\n"
        "2026-06-24T10:00:00+00:00,192.0.2.90,93.184.216.34,example.com,tcp,443\n",
        encoding="utf-8",
    )

    imported = traffic_visibility_service.import_csv(csv_path, "dns_log")
    traffic = traffic_visibility_service.list_device_traffic(created.id or 0)

    assert imported == 1
    assert traffic["recent_domains"] == ["example.com"]
    assert traffic["recent_public_ips"] == ["93.184.216.34"]
    assert traffic["rows"][0].device_id == created.id


def test_empty_or_invalid_traffic_csv_handling(traffic_visibility_service, tmp_path: Path) -> None:
    empty_csv = tmp_path / "empty.csv"
    empty_csv.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="empty or missing a header"):
        traffic_visibility_service.import_csv(empty_csv, "dns_log")

    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("timestamp,source_ip\n2026-06-24T10:00:00+00:00,192.0.2.90\n", encoding="utf-8")

    with pytest.raises(ValueError, match="missing required columns"):
        traffic_visibility_service.import_csv(bad_csv, "firewall_log")
