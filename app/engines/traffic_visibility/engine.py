from __future__ import annotations

import csv
from pathlib import Path

from app.core.models import TRAFFIC_SOURCE_TYPES, TrafficObservation, utc_now


CSV_IMPORT_SOURCE_TYPES = {"dns_log", "firewall_log", "proxy_log"}
REQUIRED_COLUMNS = {"timestamp", "source_ip", "destination_ip", "domain", "protocol", "port"}


class TrafficVisibilityEngine:
    def supported_source_types(self) -> list[str]:
        return list(TRAFFIC_SOURCE_TYPES)

    def import_csv(self, path: Path, source_type: str) -> list[TrafficObservation]:
        if source_type not in TRAFFIC_SOURCE_TYPES:
            raise ValueError("Unsupported traffic visibility source type.")
        if source_type not in CSV_IMPORT_SOURCE_TYPES:
            raise ValueError(f"{source_type} import is not implemented yet.")

        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = set(reader.fieldnames or [])
            if not reader.fieldnames:
                raise ValueError("Traffic CSV is empty or missing a header row.")
            missing = REQUIRED_COLUMNS - fieldnames
            if missing:
                missing_text = ", ".join(sorted(missing))
                raise ValueError(f"Traffic CSV is missing required columns: {missing_text}.")

            observations: list[TrafficObservation] = []
            for row in reader:
                observed_at = (row.get("timestamp") or "").strip() or utc_now()
                port_text = (row.get("port") or "").strip()
                try:
                    port = int(port_text) if port_text else None
                except ValueError as exc:
                    raise ValueError(f"Invalid port value in traffic CSV: {port_text}.") from exc

                observations.append(
                    TrafficObservation(
                        source_ip=(row.get("source_ip") or "").strip(),
                        destination_ip=(row.get("destination_ip") or "").strip() or None,
                        domain=(row.get("domain") or "").strip() or None,
                        protocol=(row.get("protocol") or "").strip().upper() or None,
                        port=port,
                        source_type=source_type,
                        observed_at=observed_at,
                    )
                )

        if not observations:
            raise ValueError("Traffic CSV did not contain any observations.")
        return observations
