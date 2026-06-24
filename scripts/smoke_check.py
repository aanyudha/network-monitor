from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.bootstrap import build_service_container


def main() -> int:
    build_service_container()
    print("Smoke check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
