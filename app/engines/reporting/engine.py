from __future__ import annotations

import csv
from pathlib import Path


class ReportingEngine:
    def export_csv(self, destination: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return destination

